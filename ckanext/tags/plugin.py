# encoding: utf-8

import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from SPARQLWrapper import SPARQLWrapper, JSON

from flask import Blueprint, render_template

from ckan.lib.base import request

VOCAB_ID = 'semantic_taxonomy_tags'

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

class ExampleIDatasetFormPlugin(plugins.SingletonPlugin,
        tk.DefaultDatasetForm):
    '''An example IDatasetForm CKAN plugin.
    Uses a tag vocabulary to add a custom metadata field to datasets.
    '''
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IRoutes, inherit=True)

    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')

        tk.add_public_directory(config, 'public')
        tk.add_resource('fanstatic', 'my_theme')

    # IBlueprint

    def get_blueprint(self):
        blueprint = Blueprint('foo', self.__module__)
        rules = [
            ('/newsemantictag', 'new_semantic_tag', new_semantic_tag)
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)

        return blueprint

    # IRoutes
    def before_map(self, map):
        map.connect('/addst', controller='ckanext.tags.controller:SemantictagsController', action='add_semantictag')
        return map

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