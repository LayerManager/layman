from flask import g
from . import util

authenticate = util.authenticate

get_open_id_claims = util.get_open_id_claims

get_iss_id = util.get_iss_id

get_sub = util.get_sub

flush_cache = util.flush_cache


def get_authn_username():
    return g.user and g.user.get('username')
