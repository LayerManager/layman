import json
import os
from layman.common.filesystem import util

AUTHN_SUBFILE = 'authn.txt'


def save_username_reservation(username, iss_id, sub, claims):
    util.ensure_whole_user(username)
    authn_path = get_authn_file(username)
    assert not os.path.isfile(authn_path)
    with open(authn_path, "w") as authn_file:
        json.dump({
            'iss_id': iss_id,
            'sub': sub,
            'claims': claims,
        }, authn_file)


def get_authn_file(username):
    uuid_file = os.path.join(util.get_user_dir(username), AUTHN_SUBFILE)
    return uuid_file


def get_authn_info(username):
    authn_path = get_authn_file(username)
    if os.path.isfile(authn_path):
        with open(authn_path) as f:
            result = json.load(f)
    else:
        result = {}
    return result
