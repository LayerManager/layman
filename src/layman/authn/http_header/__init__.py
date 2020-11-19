from flask import request, g
from layman.http import LaymanError
from layman import settings
from layman.common.prime_db_schema import users


def authenticate():
    user = None
    username = request.headers.get(settings.LAYMAN_AUTHN_HTTP_HEADER_NAME, None)
    if username is None:
        return user
    user = users.get_user_infos(username).get(username)
    if not user:
        raise LaymanError(44,
                          f'Username {username} not recognized.',
                          sub_code=1)
    user = {
        'username': username
    }
    g.user = user
    return user


def get_open_id_claims():
    return {
        'sub': g.user['username'],
        'iss': settings.LAYMAN_PROXY_SERVER_NAME,
    }


def get_iss_id():
    return __name__


def get_sub():
    return g.user['username']


def flush_cache():
    pass
