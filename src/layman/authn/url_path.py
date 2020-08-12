# remove this module
import re
from flask import request, g
from layman.util import check_username, USERNAME_RE

USER_PATH_PATTERN = re.compile('^/rest/([a-z][a-z0-9]*(?:_[a-z0-9]+)*)(?:/[^\n]*)?$')


def authenticate():
    user = None
    req_path = request.script_root + request.path
    # print(f"url_path.py req_path {req_path}")
    m = USER_PATH_PATTERN.match(req_path)
    if m is not None:
        username = m.group(1)
        check_username(username)
        user = {
            'username': username
        }
    g.user = user
    return user


def get_open_id_claims():
    username = g.user['username']
    result = {
        'iss': request.host_url,
        'sub': username,
        'preferred_username': username,
    }
    return result


def get_iss_id():
    return __name__


def get_sub():
    return g.user['username']
