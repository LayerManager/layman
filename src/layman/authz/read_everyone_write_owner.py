from flask import g, request

from layman import LaymanError
from layman.authn.url_path import USER_PATH_PATTERN


def authorize():
    if request.method in ['GET']:
        return
    elif request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
        raise LaymanError(31, {'method': request.method})

    if g.user is None:
        raise LaymanError(30, 'authenticated as anonymous user')

    username = g.user.get('name', None)
    if username is None:
        raise LaymanError(33)

    req_path = request.script_root + request.path
    m = USER_PATH_PATTERN.match(req_path)
    ownername = m.group(1)

    if username != ownername:
        raise LaymanError(30, {'user': username})

