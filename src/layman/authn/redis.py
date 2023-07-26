from flask import current_app
from layman import settings
from layman.util import get_usernames
from . import prime_db_schema

REDIS_ISSID_SUB_2_USERNAME_KEY = f"{__name__}:ISSID_SUB_2_USERNAME:{{iss_id}}:{{sub}}"


def save_username_reservation(username, iss_id, sub):
    rds = settings.LAYMAN_REDIS
    key = _get_issid_sub_2_username_key(iss_id, sub)
    rds.set(key, username)


def get_username(iss_id, sub):
    rds = settings.LAYMAN_REDIS
    key = _get_issid_sub_2_username_key(iss_id, sub)
    return rds.get(key)


def _get_issid_sub_2_username_key(iss_id, sub):
    key = REDIS_ISSID_SUB_2_USERNAME_KEY.format(iss_id=iss_id, sub=sub)
    return key


def import_authn_to_redis():
    current_app.logger.info('Importing authn to REDIS')

    usernames = get_usernames(use_cache=False)

    for username in usernames:
        authn_info = prime_db_schema.get_authn_info(username)
        if not authn_info:
            continue
        iss_id = authn_info['iss_id']
        sub = authn_info['sub']
        save_username_reservation(username, iss_id, sub)
        current_app.logger.info(
            f'Import authn into redis: username {username}, iss_id {iss_id}, sub {sub}')
