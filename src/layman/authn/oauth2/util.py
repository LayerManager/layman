from layman import settings
from layman.http import LaymanError
import importlib
import requests
from requests.exceptions import ConnectionError
from flask import request, g, current_app

FLASK_PROVIDERS_KEY = f'{__name__}:PROVIDERS'
FLASK_PROVIDER_KEY = f'{__name__}:PROVIDER'
FLASK_ACCESS_TOKEN_KEY = f'{__name__}:ACCESS_TOKEN'

ISS_URL_HEADER = 'AuthorizationIssUrl'
TOKEN_HEADER = 'Authorization'


def authenticate():
    user = None
    iss_url = request.headers.get(ISS_URL_HEADER, None)
    authz_header = request.headers.get(TOKEN_HEADER, None)
    if iss_url is None and authz_header is None:
        return user

    if iss_url is None:
        raise LaymanError(32, f'HTTP header {TOKEN_HEADER} was set, but HTTP header {ISS_URL_HEADER} was not found')
    if authz_header is None:
        raise LaymanError(32, f'HTTP header {ISS_URL_HEADER} was set, but HTTP header {TOKEN_HEADER} was not found.')

    authz_header_parts = authz_header.split(' ')
    if len(authz_header_parts) != 2:
        raise LaymanError(32, f'HTTP header {TOKEN_HEADER} must have 2 parts: "Bearer <access_token>", but has {len(authz_header_parts)} parts.')
    if authz_header_parts[0] != 'Bearer':
        raise LaymanError(32, f'First part of HTTP header {TOKEN_HEADER} must be "Bearer", but it\'s {authz_header_parts[0]}')
    access_token = authz_header_parts[1]
    if len(access_token) == 0:
        raise LaymanError(32, f'HTTP header {TOKEN_HEADER} contains empty access token. The structure must be "Bearer <access_token>"')

    provider_module = _get_provider_by_auth_url(iss_url)
    if provider_module is None:
        raise LaymanError(32, f'No OAuth2 provider was found for URL passed in HTTP header {ISS_URL_HEADER}.')

    # TODO: implement redis cache of access tokens to avoid reaching introspection endpoint on each request
    clients = settings.LIFERAY_OAUTH2_CLIENTS
    valid_resp = None
    all_connection_errors = True
    for client in clients:
        try:
            r = requests.post(provider_module.INTROSPECTION_URL, data={
                'client_id': client['id'],
                'client_secret': client['secret'],
                'token': access_token,
            })
            all_connection_errors = False
        except ConnectionError:
            continue
        if r.status_code != 200:
            raise LaymanError(32, f'Introspection endpoint returned {r.status_code} status code.')
        try:
            r_json = r.json()
            if r_json['active'] is True and r_json['token_type'] == 'Bearer':
                valid_resp = r_json
                break
        except ValueError:
            continue

    if all_connection_errors:
        raise LaymanError(32, f'Introspection endpoint is not reachable.')

    if valid_resp is None:
        raise LaymanError(32, f'Introspection endpoint claims that access token is not active or it\'s not Bearer token.')

    assert FLASK_PROVIDER_KEY not in g
    assert FLASK_ACCESS_TOKEN_KEY not in g
    g.setdefault(FLASK_PROVIDER_KEY,  provider_module)
    g.setdefault(FLASK_ACCESS_TOKEN_KEY,  access_token)

    user = {}
    g.user = user
    return user


def _get_provider_modules():
    key = FLASK_PROVIDERS_KEY
    if key not in current_app.config:
        modules = [
            importlib.import_module(m) for m in settings.AUTHN_OAUTH2_PROVIDERS
        ]
        current_app.config[key] = modules
    return current_app.config[key]


def _get_provider_module():
    key = FLASK_PROVIDER_KEY
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
    result = provider.get_open_id_claims(access_token)
    result['iss'] = provider.AUTH_URLS[0]
    return result

