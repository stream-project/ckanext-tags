import ckan.plugins as p
from ckan.lib.base import BaseController, response, request

c = p.toolkit.c
render = p.toolkit.render

VOCAB_ID = 'semantic_taxonomy_tags'


class SemantictagsController(BaseController):

    def add_semantictag(self):
        user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
        context = {'user': user['name']}
        logging.warning("addst: POST {}".format(request.POST))
        data = {'name': request.POST['tag'], 'vocabulary_id': VOCAB_ID}
        tk.get_action('tag_create')(context, data)

        return tk.render(
            'semantictags/add.html'
        )
