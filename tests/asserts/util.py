import inspect
from layman import util as layman_util, settings, app
from test_tools import process_client
from .. import Action, Publication


KEY_REPLACE = '__replace__'


def get_publication_writer(publication):
    with app.app_context():
        writer = layman_util.get_publication_writer(publication.workspace, publication.type, publication.name)
    return writer


def get_publication_header(publication):
    writer = get_publication_writer(publication)
    headers = None if writer == settings.ANONYM_USER else process_client.get_authz_headers(writer)
    return headers


def get_publication_exists(publication):
    with app.app_context():
        info = layman_util.get_publication_info(publication.workspace, publication.type, publication.name)
    return bool(info)


def get_publication_actor(publication):
    return get_publication_writer(publication)


def get_directory_name_from_publ_type(publ_type):
    return publ_type.split('.')[1] + 's'


def get_publication_uuid(publication):
    with app.app_context():
        publ_uuid = layman_util.get_publication_uuid(publication.workspace, publication.type, publication.name)
    return publ_uuid


def recursive_dict_update(base, updater, *, keep_replace_key=False):
    stack = [(base, updater)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if isinstance(current_src[key], dict) and isinstance(current_dst[key], dict) and not current_src[key].get(KEY_REPLACE):
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
                    if isinstance(current_src[key], dict) and not keep_replace_key:
                        current_src[key].pop(KEY_REPLACE, None)
    return base


def run_action(publication, action, *, cache=None):
    cache = cache or {}
    publication = Publication(
        action.params.get('workspace', publication.workspace),
        action.params.get('publ_type', publication.type),
        action.params.get('name', publication.name),
    )

    param_def = {
        'headers': Action(get_publication_header, {}),
        'actor': Action(get_publication_actor, {}),
        'rest_publication_detail': Action(process_client.get_workspace_publication, {}),
        'publ_uuid': Action(get_publication_uuid, {}),
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
        if key in method_params[0] and key not in action.params:
            if key in cache:
                value = cache[key]
            else:
                value = run_action(publication, param_method, cache=cache)
                cache[key] = value
            params[key] = value
    params.update(action.params)
    params = {key: value for key, value in params.items() if key in method_params.kwonlyargs + method_params.args}

    for key, param in params.items():
        if isinstance(param, Action):
            params[key] = run_action(publication, param, cache=cache)
    return action.method(**params)
