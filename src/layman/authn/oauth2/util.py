import importlib
import json
import math
import time
import requests
from requests.exceptions import ConnectionError
from flask import request, g, current_app

from layman import settings
from layman.http import LaymanError
from layman.authn.redis import get_username

FLASK_PROVIDERS_KEY = f'{__name__}:PROVIDERS'
FLASK_PROVIDER_KEY = f'{__name__}:PROVIDER'
FLASK_ACCESS_TOKEN_KEY = f'{__name__}:ACCESS_TOKEN'
FLASK_SUB_KEY = f'{__name__}:SUB'

ISS_URL_HEADER = 'AuthorizationIssUrl'
TOKEN_HEADER = 'Authorization'

REDIS_ACCESS_TOKEN_KEY = f'{__name__}:ISS_ACCESS_TOKEN:{{provider_module}}:{{access_token}}'


def authenticate():
    user = None
    iss_url = request.headers.get(ISS_URL_HEADER, None)
    authz_header = request.headers.get(TOKEN_HEADER, None)
    if authz_header is not None and iss_url is None and len(_get_provider_modules()) == 1:
        iss_url = _get_provider_modules()[0].AUTH_URLS[0]
        current_app.logger.info(f"\nusing default iss_url={iss_url}")
    if iss_url is None and authz_header is None:
        return user

    if iss_url is None:
        raise LaymanError(32, f'HTTP header {TOKEN_HEADER} was set, but HTTP header {ISS_URL_HEADER} was not found',
                          sub_code=1)
    if authz_header is None:
        raise LaymanError(32, f'HTTP header {ISS_URL_HEADER} was set, but HTTP header {TOKEN_HEADER} was not found.',
                          sub_code=2)

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

    provider_module = _get_provider_by_auth_url(iss_url)
    if provider_module is None:
        raise LaymanError(32, f'No OAuth2 provider was found for URL passed in HTTP header {ISS_URL_HEADER}.',
                          sub_code=6)

    access_token_info = _get_redis_access_token_info(provider_module, access_token)

    if access_token_info is None:
        # current_app.logger.info(f"Veryfying cretentials against OAuth2 provider")

        clients = settings.OAUTH2_LIFERAY_CLIENTS
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
                response = requests.post(provider_module.INTROSPECTION_URL, data=request_data,
                                         timeout=min(25 / len(clients), 15))
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

        sub = valid_resp[provider_module.INTROSPECTION_SUB_KEY]

        exp = valid_resp['exp']
        exp_in = math.ceil(exp - time.time())
        key_exp = max(min(exp_in, settings.LAYMAN_AUTHN_CACHE_MAX_TIMEOUT), 1)
        authn_info = {
            'sub': sub
        }
        # current_app.logger.info(f'Cache authn info, info={authn_info}, exp_in={exp_in}')
        _set_redis_access_token_info(provider_module, access_token, authn_info, ex=key_exp)

    else:
        # current_app.logger.info(f"Cretentials verified against Layman cache")
        sub = access_token_info['sub']

    assert FLASK_PROVIDER_KEY not in g
    assert FLASK_ACCESS_TOKEN_KEY not in g
    assert FLASK_SUB_KEY not in g
    g.setdefault(FLASK_PROVIDER_KEY, provider_module)
    g.setdefault(FLASK_ACCESS_TOKEN_KEY, access_token)
    g.setdefault(FLASK_SUB_KEY, sub)

    iss_id = get_iss_id()
    username = get_username(iss_id, sub)

    user = {}
    if username is not None:
        user['username'] = username
    # pylint: disable=assigning-non-slot
    g.user = user
    return user


def _get_provider_modules():
    key = FLASK_PROVIDERS_KEY
    if key not in current_app.config:
        modules = [
            importlib.import_module(m) for m in settings.LAYMAN_AUTHN_OAUTH2_PROVIDERS
        ]
        current_app.config[key] = modules
    return current_app.config[key]


def _get_provider_module():
    key = FLASK_PROVIDER_KEY
    return g.get(key)


def get_iss_id():
    return _get_provider_module().__name__


def get_sub():
    key = FLASK_SUB_KEY
    return g.get(key)


def _get_access_token():
    key = FLASK_ACCESS_TOKEN_KEY
    return g.get(key)


def _get_provider_by_auth_url(iss_url):
    return next((
        m for m in _get_provider_modules()
        if iss_url in m.AUTH_URLS
    ), None)


def get_open_id_claims():
    provider = _get_provider_module()
    access_token = _get_access_token()
    result = {}
    try:
        result = provider.get_open_id_claims(access_token)
    except (ConnectionError, requests.HTTPError) as err:
        current_app.logger.error(f"get_open_id_claims error:")
        current_app.logger.error(err)
        flush_cache()
    result['iss'] = provider.AUTH_URLS[0]
    return result


def _get_redis_access_token_key(provider_module, access_token):
    return REDIS_ACCESS_TOKEN_KEY.format(provider_module=provider_module.__name__, access_token=access_token)


def _get_redis_access_token_info(provider_module, access_token):
    key = _get_redis_access_token_key(provider_module, access_token)
    val = settings.LAYMAN_REDIS.get(key)
    val = json.loads(val) if val is not None else val
    return val


def _set_redis_access_token_info(provider_module, access_token, authn_info, ex=None):
    key = _get_redis_access_token_key(provider_module, access_token)
    val = json.dumps(authn_info)
    return settings.LAYMAN_REDIS.set(key, val, ex=ex)


def flush_cache():
    # current_app.logger.info(f"Flushing cache")
    provider_module = _get_provider_module()
    access_token = _get_access_token()
    key = _get_redis_access_token_key(provider_module, access_token)
    settings.LAYMAN_REDIS.delete(key)
