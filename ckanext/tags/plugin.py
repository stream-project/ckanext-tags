# encoding: utf-8

import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from SPARQLWrapper import SPARQLWrapper, JSON

from flask import Blueprint, render_template

from ckan.lib.base import request

import uuid


VOCAB_ID = 'semantic_taxonomy_tags'
global vocab_id_global
vocab_id_global = ""

def hello_plugin():
    u'''A simple view function'''
    return u'Hello World, this is served from an extension'

def recreate_semantic_taxonomy_tags():
    '''Create semantic_taxonomy_tags vocab and tags, if they don't exist already.
    Note that you could also create the vocab and tags using CKAN's API,
    and once they are created you can edit them (e.g. to add and remove
    possible dataset country code values) using the API.
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}

    sparql = SPARQLWrapper("https://sparql.stream-dataspace.net/sparql/")
    sparql.setQuery("""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?subject ?label
        FROM NAMED <http://stream-ontology.com/tags/>
        { GRAPH ?g { 
            ?subject a skos:Concept ;
              skos:prefLabel ?label . 
        } }
    """)
    sparql.setReturnFormat(JSON)
    new_tags = sparql.query().convert()

    logging.warning("vocab list {}".format(tk.get_action('vocabulary_list')(context, {})))
    existing_tags = []
    isVocabExisting = False
    vocabId = 0;
    for vocab in tk.get_action('vocabulary_list')(context, {}):
        if (vocab['name'] == VOCAB_ID):
            isVocabExisting = True
            vocabId = vocab['id']
    if isVocabExisting is True:
        logging.warning("semantic_taxonomy_tags vocabulary already exists, delete entries.")
        # remove only tags which are not present in the graph
        semantic_taxonomy_tags_ = tk.get_action('tag_list')(
            data_dict={'vocabulary_id': vocabId})

        for tag in semantic_taxonomy_tags_:
            logging.warning("Current tag \"{0}\" of vocab 'semantic_taxonomy_tags_'".format(tag))

        taglist = []
        for tag in new_tags["results"]["bindings"]:
            taglist.append(tag["label"]['value']);

        if (len(taglist) < 1):
            #Cancel because service seems to have issues
            return

        for tag in semantic_taxonomy_tags_:
            try:
                taglist.index(tag)
                existing_tags.append(tag)
            except ValueError:
                logging.warning(
                    "Removing tag {0} to vocab 'semantic_taxonomy_tags_'".format(tag))
                data = {'id': tag, 'vocabulary_id': vocabId}
                tk.get_action('tag_delete')(context, data)
    else:
        logging.warning("Creating vocab 'semantic_taxonomy_tags_'")
        data = {'name': VOCAB_ID}
        vocab = tk.get_action('vocabulary_create')(context, data)

    logging.warning("Now adding around {0} tags'".format(len(new_tags["results"]["bindings"]) - len(existing_tags)))
    for tag in new_tags["results"]["bindings"]:
        try:
            existing_tags.index(tag["label"]['value'])
        except ValueError:
            logging.warning(
                "Adding tag {0} to vocab {1}".format(tag["label"]['value'], VOCAB_ID))
            data = {'name': tag["label"]['value'], 'vocabulary_id': vocabId}
            tk.get_action('tag_create')(context, data)
    global vocab_id_global
    vocab_id_global = vocabId
    logging.warning("Id of {0} vocabulary is {1}".format(VOCAB_ID, vocabId))


def new_semantic_tag():
    return tk.render(
        'semantictags/base.html'
    )

def semantic_taxonomy_tags():
    '''Return the list of country codes from the country codes vocabulary.'''
    recreate_semantic_taxonomy_tags()
    try:
        semantic_taxonomy_tags_ = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': VOCAB_ID})
        return semantic_taxonomy_tags_
    except tk.ObjectNotFound:
        return None

def add_semantictag():
    #init
    global vocab_id_global
    tags = semantic_taxonomy_tags()

    logging.warning("addst: GET: tag {}".format(request.params.get('tag')))
    #logging.warning("Id of {0} vocabulary is {1}".format(VOCAB_ID, vocab_id_global))
    #logging.warning("tags: {}".format(tags))

    tag = request.params.get('tag')
    tagExisting = False
    for _tag in tags:
        if _tag.lower() == tag.lower():
            tagExisting = True

    if tagExisting == False:
        user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
        context = {'user': user['name']}
        data = {'name': tag, 'vocabulary_id': vocab_id_global}
        tk.get_action('tag_create')(context, data)

        # send to sparql endpoint
        sparql = SPARQLWrapper("https://sparql.stream-dataspace.net/sparql/")
        query = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX ckan: <http://stream-ontology.com/ckan/>
                INSERT DATA { GRAPH <http://stream-ontology.com/tags/> { <http://stream-ontology.com/tags/newId> a skos:Concept ; skos:prefLabel "mylabel" } }
            """
        query = query.replace("newId", str(uuid.uuid4()))
        query = query.replace("mylabel", tag)
        #logging.warning("sparql query: {}".format(query))
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        ret = sparql.query().convert()
        #logging.warning("sparql return: {}".format(ret))

    #logging.warning("all tags: {}".format(tk.get_action('tag_list')(
    #            data_dict={'vocabulary_id': VOCAB_ID})))

    return tk.render(
        'semantictags/add.html'
    )

@tk.side_effect_free
def process_tag_patch(context,data_dict=None):
    logging.warning("process_tag_patch context: {}".format(context)) # example: {u'auth_user_obj': None, u'session': <sqlalchemy.orm.scoping.scoped_session object at 0x7f4bedcb6ad0>, u'user': u'', '__auth_audit': [('process_tag_patch', 139963984044472)], u'model': <module 'ckan.model' from '/usr/lib/ckan/venv/src/ckan/ckan/model/__init__.pyc'>, u'api_version': 3}
    logging.warning("process_tag_patch data_dict: {}".format(data_dict)) # example: {u'insert': [u'555'], u'delete': [u'omega']}
    # ckan.logic.action.get.resource_search to get a resource
    # ckan.logic.action.patch.package_patch to change attributes of a resource
    global vocab_id_global

    # Authorize
    # TODO

    if "delete" in data_dict:
        for tag in data_dict["delete"]:
            # get the relevant datasets per tag
            data = {
                id: tag,
                "vocabulary_id": next(item for item in [vocab_id_global, VOCAB_ID] if item is not ""),
                "include_datasets": True
            }
            logging.warning("process_tag_patch data for details: {}".format(data))
            details = tk.get_action('tag_show')(context, data) # Validation error (Action API): "{u'__type': u'Validation Error', 'id': [u'Missing value']}"
            logging.warning("process_tag_patch tag details: {}".format(details))

            # patch the datasets
            for dataset in details["datasets"]:
                patch = {id: dataset.id}
                patch[VOCAB_ID] = dataset[VOCAB_ID].remove(tag)
                tk.patch_action('package_patch')(context, patch)

    if "insert" in data_dict:
        for tag in data_dict["delete"]:
            # get the relevant datasets per tag
            data = {
                id: tag,
                "vocabulary_id": next(item for item in [vocab_id_global, VOCAB_ID] if item is not ""),
                "include_datasets": True
            }
            logging.warning("process_tag_patch data for details: {}".format(data))
            details = tk.get_action('tag_show')(context, data) # Validation error (Action API): "{u'__type': u'Validation Error', 'id': [u'Missing value']}"
            logging.warning("process_tag_patch tag details: {}".format(details))

            # patch the datasets
            for dataset in details["datasets"]:
                patch = {id: dataset.id}
                local_tags = dataset[VOCAB_ID]
                local_tags.append(tag)
                patch[VOCAB_ID] = local_tags
                tk.patch_action('package_patch')(context, patch)


class ExampleIDatasetFormPlugin(plugins.SingletonPlugin,
        tk.DefaultDatasetForm):
    '''An example IDatasetForm CKAN plugin.
    Uses a tag vocabulary to add a custom metadata field to datasets.
    '''
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)

    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')

        tk.add_public_directory(config, 'public')
        tk.add_resource('fanstatic', 'my_theme')

    # IActions

    def get_actions(self):
        # Registers the custom API method defined above
        return {'process_tag_patch': process_tag_patch}

    # IBlueprint

    def get_blueprint(self):
        blueprint = Blueprint(self.name, self.__module__)
        rules = [
            ('/newsemantictag', 'new_semantic_tag', new_semantic_tag),
            ('/addst', 'addst', add_semantictag) # does only work with GET and not POST
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)

        return blueprint

    def get_helpers(self):
        return {VOCAB_ID: semantic_taxonomy_tags}

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):
        # Add our custom semantic_taxonomy_tags metadata field to the schema.
        schema.update({
                VOCAB_ID: [tk.get_validator('ignore_missing'),
                    tk.get_validator('tag_string_convert'),
                    tk.get_converter('convert_to_tags')(VOCAB_ID)]
                })
        return schema

    def create_package_schema(self):
        schema = super(ExampleIDatasetFormPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(ExampleIDatasetFormPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)

        logging.warning("update_package_schema: schema - keys {}".format(schema.keys()))
        logging.warning("update_package_schema: schema[tag_string] {}".format(schema['tag_string']))
        logging.warning("update_package_schema: schema[semantic_taxonomy_tags] {}".format(schema['semantic_taxonomy_tags']))
        logging.warning("update_package_schema: schema[extras] {}".format(schema['extras']))

        return schema

    def show_package_schema(self):
        schema = super(ExampleIDatasetFormPlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add our custom semantic_taxonomy_tags metadata field to the schema.
        schema.update({
            VOCAB_ID: [
                tk.get_converter('convert_from_tags')(VOCAB_ID),
                tk.get_validator('ignore_missing'),
                tk.get_validator('tag_string_convert')]
            })

        return schema