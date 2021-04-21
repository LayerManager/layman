from flask import g
from layman import settings
from . import util

authenticate = util.authenticate

get_open_id_claims = util.get_open_id_claims

get_iss_id = util.get_iss_id

get_sub = util.get_sub

flush_cache = util.flush_cache


def get_authn_username():
    anonymous = settings.ANONYM_USER
    noname = settings.NONAME_USER
    if g.user is None:
        result = anonymous
    else:
        result = g.user.get('username', noname)
    return result


def is_user_with_name(user):
    return user and user not in {settings.ANONYM_USER, settings.NONAME_USER}
