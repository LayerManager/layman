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


def get_publication_actor(publication):
    with app.app_context():
        info = layman_util.get_publication_info(publication.workspace, publication.type, publication.name, context={'keys': ['access_rights']})
    writer = info['access_rights']['write'][0]
    actor = settings.ANONYM_USER if writer == settings.RIGHTS_EVERYONE_ROLE else writer
    return actor


def same_value_for_keys(*, expected, tested, missing_key_is_ok=False):
    if isinstance(tested, dict) and isinstance(expected, dict):
        return all(
            key in tested and same_value_for_keys(expected=expected[key],
                                                  tested=tested.get(key),
                                                  missing_key_is_ok=missing_key_is_ok)
            for key in expected if
            not missing_key_is_ok or key in tested)
    return expected == tested or (missing_key_is_ok and not tested)


def get_directory_name_from_publ_type(publ_type):
    return publ_type.split('.')[1] + 's'


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
