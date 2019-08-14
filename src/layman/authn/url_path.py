import re
from flask import request, g
from layman.util import check_username

USER_PATH_PATTERN = re.compile('^/rest/([^/\n]+)(?:/[^\n]*)?$')

def authenticate():
    user = None
    req_path = request.script_root + request.path
    # print(f"url_path.py req_path {req_path}")
    m = USER_PATH_PATTERN.match(req_path)
    if m is not None:
        username = m.group(1)
        check_username(username)
        user = {
            'name': username
        }
    g.user = user
    return user


