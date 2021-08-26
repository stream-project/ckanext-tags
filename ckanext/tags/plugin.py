# encoding: utf-8

import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk


def create_semantic_taxonomy_tags():
    '''Create semantic_taxonomy_tags vocab and tags, if they don't exist already.
    Note that you could also create the vocab and tags using CKAN's API,
    and once they are created you can edit them (e.g. to add and remove
    possible dataset country code values) using the API.
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'semantic_taxonomy_tags'}
        tk.get_action('vocabulary_show')(context, data)
        logging.info("Example genre vocabulary already exists, skipping.")
    except tk.ObjectNotFound:
        logging.info("Creating vocab 'semantic_taxonomy_tags'")
        data = {'name': 'semantic_taxonomy_tags'}
        vocab = tk.get_action('vocabulary_create')(context, data)
        for tag in (u'uk', u'ie', u'de', u'fr', u'es'):
            logging.info(
                    "Adding tag {0} to vocab 'semantic_taxonomy_tags'".format(tag))
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tk.get_action('tag_create')(context, data)


def semantic_taxonomy_tags():
    '''Return the list of country codes from the country codes vocabulary.'''
    create_semantic_taxonomy_tags()
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