import inspect
from layman import util as layman_util, settings, app
from test_tools import process_client


def get_publication_header(publication):
    with app.app_context():
        info = layman_util.get_publication_info(publication.workspace, publication.type, publication.name, context={'keys': ['access_rights']})
    writer = info['access_rights']['write'][0]
    headers = None if writer == settings.RIGHTS_EVERYONE_ROLE else process_client.get_authz_headers(writer)
    return headers


def get_publication_actor(publication):
    with app.app_context():
        info = layman_util.get_publication_info(publication.workspace, publication.type, publication.name, context={'keys': ['access_rights']})
    writer = info['access_rights']['write'][0]
    actor = settings.ANONYM_USER if writer == settings.RIGHTS_EVERYONE_ROLE else writer
    return actor


def run_action(publication, action, *, cache=None):
    param_def = {
        'headers': get_publication_header,
        'actor': get_publication_header,
    }
    method_params = inspect.getfullargspec(action.method)
    publ_type_param = 'publication_type' if 'publication_type' in method_params[0] else 'publ_type'
    params = {
        publ_type_param: publication.type,
        'workspace': publication.workspace,
        'name': publication.name,
    }
    for param, param_method in param_def.items():
        if param in method_params[0]:
            if param in cache:
                value = cache[param]
            else:
                value = param_method(publication)
                cache[param] = value
            params[param] = value
    params.update(action.params)
    action.method(**params)
