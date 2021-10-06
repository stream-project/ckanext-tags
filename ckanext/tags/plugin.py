# encoding: utf-8

import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON
import ssl

# Very bad code - should be removed for production!
ssl._create_default_https_context = ssl._create_unverified_context
# Reason is that python 2.x seems to have issues with SSL since 2021-10-01

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

    try:
        data = {'id': 'semantic_taxonomy_tags'}
        vocab = tk.get_action('vocabulary_show')(context, data)
        logging.warning("semantic_taxonomy_tags vocabulary already exists, delete entries.")
        # remove only tags which are not present in the graph
        semantic_taxonomy_tags = tk.get_action('tag_list')(
            data_dict={'vocabulary_id': 'semantic_taxonomy_tags'})

        for tag in semantic_taxonomy_tags:
            logging.warning("Current tag \"{0}\" of vocab 'semantic_taxonomy_tags'".format(tag))

        taglist = []
        existing_tags = []
        for tag in new_tags["results"]["bindings"]:
            taglist.append(tag["label"]['value']);

        if (len(taglist) < 1):
            #Cancel because service seems to have issues
            return

        for tag in semantic_taxonomy_tags:
            try:
                taglist.index(tag)
                existing_tags.append(tag)
            except ValueError:
                logging.warning(
                    "Removing tag {0} to vocab 'semantic_taxonomy_tags'".format(tag))
                data = {'id': tag, 'vocabulary_id': 'semantic_taxonomy_tags'}
                tk.get_action('tag_delete')(context, data)

    except tk.ObjectNotFound:
        logging.warning("Creating vocab 'semantic_taxonomy_tags'")
        data = {'name': 'semantic_taxonomy_tags'}
        vocab = tk.get_action('vocabulary_create')(context, data)

    logging.warning("Now adding around {0} tags'".format(len(new_tags["results"]["bindings"]) - len(existing_tags)))
    for tag in new_tags["results"]["bindings"]:
        try:
            existing_tags.index(tag["label"]['value'])
        except ValueError:
            logging.warning(
                "Adding tag {0} to vocab 'semantic_taxonomy_tags'".format(tag["label"]['value']))
            data = {'name': tag["label"]['value'], 'vocabulary_id': vocab['id']}
            tk.get_action('tag_create')(context, data)



def semantic_taxonomy_tags():
    '''Return the list of country codes from the country codes vocabulary.'''
    recreate_semantic_taxonomy_tags()
    try:
        semantic_taxonomy_tags = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': 'semantic_taxonomy_tags'})
        return semantic_taxonomy_tags
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

    # These record how many times methods that this plugin's methods are
    # called, for testing purposes.
    num_times_new_template_called = 0
    num_times_read_template_called = 0
    num_times_edit_template_called = 0
    num_times_search_template_called = 0
    num_times_history_template_called = 0
    num_times_package_form_called = 0
    num_times_check_data_dict_called = 0
    num_times_setup_template_variables_called = 0

    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')

    def get_helpers(self):
        return {'semantic_taxonomy_tags': semantic_taxonomy_tags}

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
                'semantic_taxonomy_tags': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_tags')('semantic_taxonomy_tags')]
                })
        return schema

    def create_package_schema(self):
        schema = super(ExampleIDatasetFormPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(ExampleIDatasetFormPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(ExampleIDatasetFormPlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add our custom semantic_taxonomy_tags metadata field to the schema.
        schema.update({
            'semantic_taxonomy_tags': [
                tk.get_converter('convert_from_tags')('semantic_taxonomy_tags'),
                tk.get_validator('ignore_missing')]
            })

        return schema

    # These methods just record how many times they're called, for testing
    # purposes.
    # TODO: It might be better to test that custom templates returned by
    # these methods are actually used, not just that the methods get
    # called.

    def setup_template_variables(self, context, data_dict):
        ExampleIDatasetFormPlugin.num_times_setup_template_variables_called += 1
        return super(ExampleIDatasetFormPlugin, self).setup_template_variables(
                context, data_dict)

    def new_template(self):
        ExampleIDatasetFormPlugin.num_times_new_template_called += 1
        return super(ExampleIDatasetFormPlugin, self).new_template()

    def read_template(self):
        ExampleIDatasetFormPlugin.num_times_read_template_called += 1
        return super(ExampleIDatasetFormPlugin, self).read_template()

    def edit_template(self):
        ExampleIDatasetFormPlugin.num_times_edit_template_called += 1
        return super(ExampleIDatasetFormPlugin, self).edit_template()

    def search_template(self):
        ExampleIDatasetFormPlugin.num_times_search_template_called += 1
        return super(ExampleIDatasetFormPlugin, self).search_template()

    def history_template(self):
        ExampleIDatasetFormPlugin.num_times_history_template_called += 1
        return super(ExampleIDatasetFormPlugin, self).history_template()

    def package_form(self):
        ExampleIDatasetFormPlugin.num_times_package_form_called += 1
        return super(ExampleIDatasetFormPlugin, self).package_form()

    # check_data_dict() is deprecated, this method is only here to test that
    # legacy support for the deprecated method works.
    def check_data_dict(self, data_dict, schema=None):
        ExampleIDatasetFormPlugin.num_times_check_data_dict_called += 1