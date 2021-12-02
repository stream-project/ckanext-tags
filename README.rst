=============
ckanext-tags
=============

.. Put a description of your extension here:
   What does it do? What features does it have?
   Consider including some screenshots or embedding a video!

This extension does add semantic tags to datasets. It is conneted to a SPARQL endpoint. For more details see task 4.4 of the STREAM project.

It is based on CKAN official example https://docs.ckan.org/en/2.9/extensions/adding-custom-fields.html

------------
Requirements
------------

See requirements.txt


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

Inside Dockerfile:

```
ADD ./Plugins/ckanext-tags $CKAN_HOME/src/ckanext-tags
RUN ckan-pip install -e $CKAN_HOME/src/ckanext-tags
RUN ckan-pip install -r $CKAN_HOME/src/ckanext-tags/requirements.txt
```
