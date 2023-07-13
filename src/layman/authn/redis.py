from flask import current_app
from layman import settings
from layman.util import get_usernames
from . import filesystem

REDIS_ISSID_SUB_2_USERNAME_KEY = f"{__name__}:ISSID_SUB_2_USERNAME:{{sub}}"


def save_username_reservation(username, sub):
    rds = settings.LAYMAN_REDIS
    key = _get_issid_sub_2_username_key(sub)
    rds.set(key, username)


def get_username(sub):
    rds = settings.LAYMAN_REDIS
    key = _get_issid_sub_2_username_key(sub)
    return rds.get(key)


def _get_issid_sub_2_username_key(sub):
    key = REDIS_ISSID_SUB_2_USERNAME_KEY.format(sub=sub)
    return key


def import_authn_to_redis():
    current_app.logger.info('Importing authn to REDIS')

    usernames = get_usernames(use_cache=False)

    for username in usernames:
        authn_info = filesystem.get_authn_info(username)
        if not authn_info:
            continue
        sub = authn_info['sub']
        save_username_reservation(username, sub)
        current_app.logger.info(
            f'Import authn into redis: username {username}, sub {sub}')
