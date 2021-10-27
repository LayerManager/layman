import inspect
from layman import util as layman_util, settings, app
from test_tools import process_client
from .. import Action


def get_publication_header(publication):
    with app.app_context():
        info = layman_util.get_publication_info(publication.workspace, publication.type, publication.name, context={'keys': ['access_rights']})
    writer = info['access_rights']['write'][0]
    headers = None if writer == settings.RIGHTS_EVERYONE_ROLE else process_client.get_authz_headers(writer)
    return headers


def get_publication_exists(publication):
    with app.app_context():
        info = layman_util.get_publication_info(publication.workspace, publication.type, publication.name)
    return bool(info)


def get_publication_actor(publication):
    with app.app_context():
        info = layman_util.get_publication_info(publication.workspace, publication.type, publication.name, context={'keys': ['access_rights']})
    writer = info['access_rights']['write'][0]
    actor = settings.ANONYM_USER if writer == settings.RIGHTS_EVERYONE_ROLE else writer
    return actor


def get_directory_name_from_publ_type(publ_type):
    return publ_type.split('.')[1] + 's'


def recursive_dict_update(base, updater):
    stack = [(base, updater)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if isinstance(current_src[key], dict) and isinstance(current_dst[key], dict):
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
    return base


def run_action(publication, action, *, cache=None):
    param_def = {
        'headers': Action(get_publication_header, dict()),
        'actor': Action(get_publication_actor, dict()),
        'rest_publication_detail': Action(process_client.get_workspace_publication, dict())
    }
    method_params = inspect.getfullargspec(action.method)
    publ_type_param = 'publication_type' if 'publication_type' in method_params[0] else 'publ_type'
    params = {}
    for key, value in {publ_type_param: publication.type,
                       'workspace': publication.workspace,
                       'name': publication.name,
                       'publication': publication, }.items():
        if key in method_params[0]:
            params[key] = value

    for key, param_method in param_def.items():
        if key in method_params[0]:
            if key in cache:
                value = cache[key]
            else:
                value = run_action(publication, param_method, cache=cache)
                cache[key] = value
            params[key] = value
    params.update(action.params)
    return action.method(**params)
