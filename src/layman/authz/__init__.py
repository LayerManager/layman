from functools import wraps
from flask import g, request

from layman import LaymanError
from layman.authn.url_path import USER_PATH_PATTERN


def authorize(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # print(f"authorize ARGS {args} KWARGS {kwargs}")
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            pass

        if g.user is None:
            raise LaymanError(30, 'authenticated as anonymous user')

        username = g.user['name']

        req_path = request.script_root + request.path
        m = USER_PATH_PATTERN.match(req_path)
        ownername = m.group(1)

        if username != ownername:
            raise LaymanError(30, {'user': username})

        return f(*args, **kwargs)
    return decorated_function


