import json
from functools import wraps
from flask import after_this_request, request

from layman import LaymanError, settings, authn, util as layman_util, common
from layman.common.prime_db_schema import workspaces, users
from layman.common.rest import parse_request_path
from . import role_service


def authorize(workspace, publication_type, publication_name, request_method, actor_name):
    is_multi_publication_request = not publication_name

    publication_not_found_code = {
        'layman.layer': 15,
        'layman.map': 26,
    }[publication_type]

    if is_multi_publication_request:
        if request_method.lower() in [common.REQUEST_METHOD_GET, common.REQUEST_METHOD_DELETE]:
            if not workspaces.get_workspace_infos(workspace):
                raise LaymanError(40)  # Workspace not found
            return
        if request_method.lower() in [common.REQUEST_METHOD_POST]:
            if actor_name == workspace:
                return
            if ((not users.get_user_infos(workspace))  # public workspace
                    and can_user_publish_in_public_workspace(actor_name)):  # actor can publish in public workspace
                if workspaces.get_workspace_infos(workspace):  # workspaces exists
                    return
                if can_user_create_public_workspace(actor_name):  # workspaces can be created by actor
                    # raises exception if new workspace is not correct
                    layman_util.check_workspace_name(workspace)
                else:
                    raise LaymanError(30)  # unauthorized request
            else:
                raise LaymanError(30)  # unauthorized request
        else:
            raise LaymanError(31, {'method': request_method})  # unsupported method
    else:
        if not workspaces.get_workspace_infos(workspace):
            raise LaymanError(40)  # Workspace not found
        publ_info = layman_util.get_publication_infos(workspace, publication_type, publ_name=publication_name).get(
            (workspace, publication_type, publication_name)
        )
        if not publ_info:
            raise LaymanError(publication_not_found_code)
        user_can_read = is_user_in_access_rule(actor_name, publ_info['access_rights']['read'])
        if request_method.lower() in [common.REQUEST_METHOD_GET]:
            if user_can_read:
                return
            raise LaymanError(publication_not_found_code)
        if request_method.lower() in [common.REQUEST_METHOD_PATCH, common.REQUEST_METHOD_DELETE,
                                      common.REQUEST_METHOD_POST, common.REQUEST_METHOD_PUT, ]:
            if is_user_in_access_rule(actor_name, publ_info['access_rights']['write']):
                return
            if user_can_read:
                raise LaymanError(30)  # unauthorized request
            raise LaymanError(publication_not_found_code)
        raise LaymanError(31, {'method': request_method})  # unsupported method


def authorize_after_multi_get_request(actor_name, response):
    # print(f"authorize_after_request, status_code = {response.status_code}, workspace={workspace}, actor_name={actor_name}")
    if response.status_code == 200:
        publications_json = json.loads(response.get_data())
        publications_json = [
            publication_json for publication_json in publications_json
            if is_user_in_access_rule(actor_name, publication_json['access_rights']['read'])
        ]
        response.set_data(json.dumps(publications_json))
    return response


def is_user_in_access_rule(username, access_rule_names):
    usernames, rolenames = split_user_and_role_names(access_rule_names)
    userroles = role_service.get_user_roles(username)
    return settings.RIGHTS_EVERYONE_ROLE in rolenames \
        or (username and username in usernames) \
        or (set(rolenames).intersection(userroles))


def can_user_publish_in_public_workspace(username):
    return is_user_in_access_rule(username, settings.GRANT_PUBLISH_IN_PUBLIC_WORKSPACE)


def can_user_create_public_workspace(username):
    return is_user_in_access_rule(username, settings.GRANT_CREATE_PUBLIC_WORKSPACE)


def can_user_write_publication(*, username, uuid):
    publ_info = layman_util.get_publication_info_by_uuid(uuid=uuid, context={'keys': ['access_rights']})
    return publ_info and is_user_in_access_rule(username, publ_info['access_rights']['write'])


def can_i_edit(*, uuid):
    actor_name = authn.get_authn_username()
    return can_user_write_publication(username=actor_name, uuid=uuid)


def authorize_workspace_publications_decorator(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # print(f"authorize ARGS {args} KWARGS {kwargs}")
        req_path = request.script_root + request.path
        (workspace, publication_type, publication_name) = parse_request_path(req_path)
        if workspace is None or publication_type is None:
            raise Exception(f"Authorization module is unable to authorize path {req_path}")
        actor_name = authn.get_authn_username()
        # raises exception in case of unauthorized request
        authorize(workspace, publication_type, publication_name, request.method, actor_name)
        if workspace and publication_type and not publication_name and request.method.lower() == common.REQUEST_METHOD_GET:
            # pylint: disable=unused-variable
            @after_this_request
            def authorize_after_request_tmp(response):
                return authorize_after_multi_get_request(actor_name, response)
        return func(*args, **kwargs)

    return decorated_function


def authorize_uuid_publication_decorator(*, expected_publication_type):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            uuid = request.view_args['uuid']
            info = layman_util.get_publication_info_by_uuid(uuid, context={'keys': ['workspace', 'name', 'type']})
            if info is None or info.get('type') != expected_publication_type:
                raise LaymanError(26, {'uuid': uuid})
            workspace = info['_workspace']
            publication_type = info['type']
            publication_name = info['name']
            actor_name = authn.get_authn_username()
            # raises exception in case of unauthorized request
            authorize(workspace, publication_type, publication_name, request.method, actor_name)
            return func(*args, **kwargs)
        return decorated_function

    return decorator


def authorize_publications_decorator(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # print(f"authorize ARGS {args} KWARGS {kwargs}")
        req_path = request.script_root + request.path
        (workspace, _, publication_name) = parse_request_path(req_path)
        if workspace or publication_name:
            raise Exception(f"Authorization module is unable to authorize path {req_path}")
        actor_name = authn.get_authn_username()
        if request.method.lower() == common.REQUEST_METHOD_GET:
            # pylint: disable=unused-variable
            @after_this_request
            def authorize_after_request_tmp(response):
                return authorize_after_multi_get_request(actor_name, response)
        return func(*args, **kwargs)

    return decorated_function


def complete_access_rights(access_rights_to_complete, full_access_rights):
    access_rights_to_complete = access_rights_to_complete or {}
    for right_type in ['read', 'write']:
        if right_type not in access_rights_to_complete:
            access_rights_to_complete[right_type] = full_access_rights[right_type]
    return access_rights_to_complete


def is_user(user_or_role_name):
    return any(letter.islower() for letter in user_or_role_name)


def split_user_and_role_names(user_and_role_names):
    user_names = [name for name in user_and_role_names if is_user(name)]
    role_names = [name for name in user_and_role_names if name not in user_names]
    return user_names, role_names


def is_allowed_to_delete_user(*, username, actor_name):
    if not username:
        return False
    if actor_name == username:
        return True
    return is_user_in_access_rule(actor_name, settings.GRANT_DELETE_OTHER_USER)
