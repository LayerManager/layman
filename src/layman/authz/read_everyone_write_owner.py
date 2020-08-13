from flask import g, request

from layman import LaymanError
from layman.authn.url_path import USER_PATH_PATTERN

from layman.common import geoserver as gs


def authorize():
    if request.method in ['GET']:
        return
    elif request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
        raise LaymanError(31, {'method': request.method})

    if g.user is None:
        raise LaymanError(30, 'authenticated as anonymous user')

    username = g.user.get('username', None)
    if request.method == 'POST' and username is None:
        raise LaymanError(33)

    req_path = request.script_root + request.path
    m = USER_PATH_PATTERN.match(req_path)
    ownername = m.group(1) if m is not None else None

    if ownername is None and request.path == '/rest/current-user':
        return

    if username != ownername or ownername is None or len(ownername) == 0:
        raise LaymanError(30, {'username': username})


def get_publication_access_rights(publ_type, username, publication_name):
    return {
        'guest': 'r',
    }


def get_gs_roles(username, type):
    if type == 'r':
        roles = gs.get_roles_anyone(username)
    elif type == 'w':
        roles = gs.get_roles_owner(username)
    return roles
