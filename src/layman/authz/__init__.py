import json
from flask import after_this_request
from functools import wraps
from layman.common.prime_db_schema import workspaces, users, publications
from . import util


from flask import g, request
import re

from layman import LaymanError, settings
from layman.util import USERNAME_ONLY_PATTERN
from layman.common.util import PUBLICATION_NAME_ONLY_PATTERN


def _get_multi_publication_path_pattern():
    workspace_pattern = r"(?P<workspace>" + USERNAME_ONLY_PATTERN + r")"
    # TODO generate layers|maps automatically from blueprints using settings.PUBLICATION_MODULES
    publ_type_pattern = r"(?P<publication_type>layers|maps)"
    return "^/rest/" + workspace_pattern + "/" + publ_type_pattern


MULTI_PUBLICATION_PATH_PATTERN = re.compile(_get_multi_publication_path_pattern() + r"/?$")
SINGLE_PUBLICATION_PATH_PATTERN = re.compile(
    _get_multi_publication_path_pattern() + r"/(?P<publication_name>" + PUBLICATION_NAME_ONLY_PATTERN + r")(?:/.*)?$"
)


from layman.common import geoserver as gs


def parse_request_path(request_path):
    workspace = None
    publication_type = None
    publication_type_url_prefix = None
    publication_name = None
    m = MULTI_PUBLICATION_PATH_PATTERN.match(request_path)
    if not m:
        m = SINGLE_PUBLICATION_PATH_PATTERN.match(request_path)
    if m:
        workspace = m.group('workspace')
        publication_type_url_prefix = m.group('publication_type')
        publication_name = m.groupdict().get('publication_name', None)
    if publication_type_url_prefix:
        # TODO get it using settings.PUBLICATION_MODULES
        publication_type = {
            'layers': 'layman.layer',
            'maps': 'layman.map',
        }[publication_type_url_prefix]
    if workspace in settings.RESERVED_WORKSPACE_NAMES:
        workspace = None
    return (workspace, publication_type, publication_name)


def authorize(workspace, publication_type, publication_name, request_method, actor_name):
    if workspace is None:
        raise Exception(f"Authorization module is unable to authorize path {request_path}")

    is_multi_publication_request = not publication_name

    publication_not_found_code = {
        'layman.layer': 15,
        'layman.map': 26,
    }[publication_type]

    if is_multi_publication_request:
        if request_method in ['GET']:
            return
        elif request_method in ['POST']:
            if actor_name == workspace:
                return
            elif ((not users.get_user_infos(workspace).get(workspace)) and  # public workspace
                    (
                        workspaces.get_workspace_infos(workspace).get(workspace) or  # either exists
                        can_user_create_public_workspace(actor_name)  # or can be created by actor
                    ) and can_user_publish_in_public_workspace(actor_name)):  # actor can publish there
                return
            else:
                raise LaymanError(30)
        else:
            raise LaymanError(31, {'method': request_method})
    else:
        publ_info = publications.get_publication_infos(workspace, publication_type).get(
            (workspace, publication_name, publication_type)
        )
        publ_exists = bool(publ_info)
        if not publ_exists:
            raise LaymanError(publication_not_found_code)
        user_can_read = is_user_in_access_rule(actor_name, publ_info['access_rights']['read'])
        if request_method in ['GET']:
            if user_can_read:
                return
            else:
                raise LaymanError(publication_not_found_code)
        elif request_method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            if is_user_in_access_rule(actor_name, publ_info['access_rights']['write']):
                return
            elif user_can_read:
                raise LaymanError(30)
            else:
                raise LaymanError(publication_not_found_code)
        else:
            raise LaymanError(31, {'method': request_method})


def authorize_after_multi_get_request(workspace, actor_name, response):
    # print(f"authorize_after_request, status_code = {response.status_code}, workspace={workspace}, actor_name={actor_name}")
    if response.status_code == 200:
        publication_infos = publications.get_publication_infos(workspace_name=workspace)
        # print(f"authorize_after_request, publication_infos = {publication_infos}")
        safe_uuids = [
            publication_info['uuid'] for publication_info in publication_infos.values()
            if is_user_in_access_rule(actor_name, publication_info['access_rights']['read'])
        ]
        # print(f"authorize_after_request, safe_uuids = {safe_uuids}")
        publications_json = json.loads(response.get_data())
        publications_json = [
            publication_json for publication_json in publications_json
            if publication_json['uuid'] in safe_uuids
        ]
        response.set_data(json.dumps(publications_json))
    return response


def get_publication_access_rights(publ_type, username, publication_name):
    # TODO consult with Franta/Raitis not using groups for map JSON anymore
    return {}


def get_gs_roles(username, type):
    # TODO consider functionality
    if type == 'r':
        roles = gs.get_roles_anyone(username)
    elif type == 'w':
        roles = gs.get_roles_owner(username)
    return roles


def is_user_in_access_rule(username, access_rule_names):
    return settings.RIGHTS_EVERYONE_ROLE in access_rule_names \
           or (username and username in access_rule_names)


def can_user_publish_in_public_workspace(username):
    return is_user_in_access_rule(username, settings.GRANT_PUBLISH_IN_PUBLIC_WORKSPACE)


def can_user_create_public_workspace(username):
    return is_user_in_access_rule(username, settings.GRANT_CREATE_PUBLIC_WORKSPACE)


def can_i_edit(publ_type, username, publication_name):
    # TODO consider functionality
    return g.user is not None and g.user['username'] == username


def authorize_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # print(f"authorize ARGS {args} KWARGS {kwargs}")
        req_path = request.script_root + request.path
        (workspace, publication_type, publication_name) = parse_request_path(req_path)
        if workspace is None or publication_type is None:
            raise Exception(f"Authorization module is unable to authorize path {req_path}")
        actor_name = g.user and g.user['username']
        authorize(workspace, publication_type, publication_name, request.method, actor_name)
        if workspace and publication_type and not publication_name and request.method == 'GET':
            @after_this_request
            def authorize_after_request_tmp(response):
                return authorize_after_multi_get_request(workspace, actor_name, response)
        return f(*args, **kwargs)

    return decorated_function


# TODO re-think
get_all_gs_roles = util.get_all_gs_roles
