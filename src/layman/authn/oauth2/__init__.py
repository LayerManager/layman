import json
import math
import time
import requests
from requests.exceptions import ConnectionError
from flask import request, g, current_app

from layman import settings
from layman.http import LaymanError
from layman.authn.redis import get_username


AUTH_URLS = settings.OAUTH2_AUTH_URLS
INTROSPECTION_URL = settings.OAUTH2_INTROSPECTION_URL
INTROSPECTION_SUB_KEY = settings.OAUTH2_INTROSPECTION_SUB_KEY
USER_PROFILE_URL = settings.OAUTH2_USER_PROFILE_URL

FLASK_ACCESS_TOKEN_KEY = f'{__name__}:ACCESS_TOKEN'
FLASK_SUB_KEY = f'{__name__}:SUB'
REDIS_ACCESS_TOKEN_KEY = f'{__name__}:ACCESS_TOKEN:{{access_token}}'
TOKEN_HEADER = 'Authorization'


def authenticate():
    user = None
    authz_header = request.headers.get(TOKEN_HEADER, None)
    if authz_header is None:
        return user

    authz_header_parts = authz_header.split(' ')
    if len(authz_header_parts) != 2:
        raise LaymanError(32,
                          f'HTTP header {TOKEN_HEADER} must have 2 parts: "Bearer <access_token>", but has {len(authz_header_parts)} parts.',
                          sub_code=3)
    if authz_header_parts[0] != 'Bearer':
        raise LaymanError(32,
                          f'First part of HTTP header {TOKEN_HEADER} must be "Bearer", but it\'s {authz_header_parts[0]}',
                          sub_code=4)
    access_token = authz_header_parts[1]
    if len(access_token) == 0:
        raise LaymanError(32,
                          f'HTTP header {TOKEN_HEADER} contains empty access token. The structure must be "Bearer <access_token>"',
                          sub_code=5)

    access_token_info = _get_redis_access_token_info(access_token)

    if access_token_info is None:
        # current_app.logger.info(f"Veryfying cretentials against OAuth2 provider")

        clients = settings.OAUTH2_CLIENTS
        valid_resp = None
        all_connection_errors = True
        for client in clients:
            try:
                request_data = {
                    k: v for k, v in
                    {
                        'client_id': client['id'],
                        'client_secret': client['secret'],
                        'token': access_token,
                    }.items()
                    if v is not None
                }
                response = requests.post(INTROSPECTION_URL, data=request_data, timeout=min(25 / len(clients), 15))
                if response.status_code != 200:
                    continue
                all_connection_errors = False
            except ConnectionError:
                continue
            try:
                r_json = response.json()
                # current_app.logger.info(f"r_json={r_json}")
                if r_json['active'] is True and r_json.get('token_type', 'Bearer') == 'Bearer':
                    valid_resp = r_json
                    break
            except ValueError:
                continue

        if all_connection_errors:
            raise LaymanError(32, f'Introspection endpoint is not reachable or returned status code other than 200.',
                              sub_code=8)

        if valid_resp is None:
            raise LaymanError(32,
                              f'Introspection endpoint claims that access token is not active or it\'s not Bearer token.',
                              sub_code=9)

        sub = valid_resp[INTROSPECTION_SUB_KEY]

        exp = valid_resp['exp']
        exp_in = math.ceil(exp - time.time())
        key_exp = max(min(exp_in, settings.LAYMAN_AUTHN_CACHE_MAX_TIMEOUT), 1)
        authn_info = {
            'sub': sub
        }
        # current_app.logger.info(f'Cache authn info, info={authn_info}, exp_in={exp_in}')
        _set_redis_access_token_info(access_token, authn_info, ex=key_exp)

    else:
        # current_app.logger.info(f"Cretentials verified against Layman cache")
        sub = access_token_info['sub']

    assert FLASK_ACCESS_TOKEN_KEY not in g
    assert FLASK_SUB_KEY not in g
    g.setdefault(FLASK_ACCESS_TOKEN_KEY, access_token)
    g.setdefault(FLASK_SUB_KEY, sub)

    username = get_username(sub)

    user = {}
    if username is not None:
        user['username'] = username
    # pylint: disable=assigning-non-slot
    g.user = user
    return user


def get_open_id_claims():
    access_token = _get_access_token()
    result = {}
    try:
        response = requests.get(USER_PROFILE_URL, headers={
            'Authorization': f'Bearer {access_token}',
        }, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        response.raise_for_status()
        r_json = response.json()
        result['sub'] = r_json['userId']
        result['email'] = r_json['emailAddress']
        result['email_verified'] = r_json['emailAddressVerified']
        name = [
            n for n in [
                r_json.get('firstName', None),
                r_json.get('middleName', None),
                r_json.get('lastName', None)
            ]
            if n is not None and len(n) > 0
        ]
        name = " ".join(name)
        result['name'] = name
        result['given_name'] = r_json.get('firstName')
        result['family_name'] = r_json.get('lastName')
        result['middle_name'] = r_json.get('middleName')
        result['preferred_username'] = r_json.get('screenName')
        result['updated_at'] = r_json.get('modifiedDate')
    except (ConnectionError, requests.HTTPError) as err:
        current_app.logger.error(f"get_open_id_claims error:")
        current_app.logger.error(err)
        flush_cache()
    result['iss'] = AUTH_URLS[0]
    return result


def get_iss_id():
    return __name__


def get_sub():
    key = FLASK_SUB_KEY
    return g.get(key)


def flush_cache():
    # current_app.logger.info(f"Flushing cache")
    access_token = _get_access_token()
    key = _get_redis_access_token_key(access_token)
    settings.LAYMAN_REDIS.delete(key)


def _get_access_token():
    key = FLASK_ACCESS_TOKEN_KEY
    return g.get(key)


def _get_redis_access_token_key(access_token):
    return REDIS_ACCESS_TOKEN_KEY.format(access_token=access_token)


def _get_redis_access_token_info(access_token):
    key = _get_redis_access_token_key(access_token)
    val = settings.LAYMAN_REDIS.get(key)
    val = json.loads(val) if val is not None else val
    return val


def _set_redis_access_token_info(access_token, authn_info, ex=None):
    key = _get_redis_access_token_key(access_token)
    val = json.dumps(authn_info)
    return settings.LAYMAN_REDIS.set(key, val, ex=ex)
