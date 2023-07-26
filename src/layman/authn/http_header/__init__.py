from flask import request, g
from layman.http import LaymanError
from layman import settings
from layman.common.prime_db_schema import users


def authenticate():
    actor = None
    actor_name = request.headers.get(settings.LAYMAN_AUTHN_HTTP_HEADER_NAME, None)
    if actor_name is None:
        return actor
    actor = users.get_user_infos(actor_name).get(actor_name)
    if not actor:
        raise LaymanError(44,
                          f'Username {actor_name} not recognized.',
                          sub_code=1)
    actor = {
        'username': actor_name
    }
    # pylint: disable=assigning-non-slot
    g.user = actor
    return actor


def get_open_id_claims():
    return {
        'sub': g.user['username'],
        'iss': get_iss(),
    }


def get_iss_id():
    return 'layman.authn.http_header'


def get_iss():
    return settings.LAYMAN_PROXY_SERVER_NAME


def get_sub():
    return g.user['username']


def flush_cache():
    pass
