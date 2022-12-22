=============
ckanext-tags
=============

This extension does add semantic tags to datasets. It is connected to a SPARQL endpoint. For more details see task 4.4 of the STREAM project.

It is based on CKAN official example https://docs.ckan.org/en/2.9/extensions/adding-custom-fields.html

------------
Requirements
------------

See requirements.txt


------------
Installation
------------

Inside Dockerfile:

```
ADD ./Plugins/ckanext-tags $CKAN_HOME/src/ckanext-tags
RUN ckan-pip install -e $CKAN_HOME/src/ckanext-tags
RUN ckan-pip install -r $CKAN_HOME/src/ckanext-tags/requirements.txt
```

------------
TODOs
------------

* See Todos in Code
* make the SPARQL URI a env
