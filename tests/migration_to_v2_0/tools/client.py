from __future__ import annotations

import json
import logging

import requests
import layman_settings as settings
from .http import LaymanError

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 15

TOKEN_HEADER = 'Authorization'


def get_authz_headers(username):
    return {f'{TOKEN_HEADER}': f'Bearer {username}'}


def raise_layman_error(response, status_codes_to_skip=None):
    status_codes_to_skip = status_codes_to_skip or set()
    status_codes_to_skip.add(200)
    if 400 <= response.status_code < 500 and response.status_code not in status_codes_to_skip:
        details = json.loads(response.text)
        raise LaymanError(details['code'],
                          details.get('detail'),
                          http_code=response.status_code,
                          sub_code=details.get('sub_code'))
    if response.status_code not in status_codes_to_skip:
        logger.error(f'raise_layman_error: response.status_code={response.status_code}, response.text={response.text}')
        response.raise_for_status()
    assert response.status_code in status_codes_to_skip, f"response.status_code={response.status_code}\nresponse.text={response.text}"
    assert 'Deprecation' not in response.headers, f'This is deprecated URL! Use new one. headers={response.headers}'


class RestClient:

    def __init__(self, base_url: str):
        self.base_url: str = base_url

    def reserve_username(self, username, headers=None, *, actor_name=None):
        headers = headers or {}
        if actor_name:
            assert TOKEN_HEADER not in headers

        if actor_name and actor_name != settings.ANONYM_USER:
            headers.update(get_authz_headers(actor_name))
        r_url = f"{self.base_url}/rest/current-user"
        data = {
            'username': username,
        }
        response = requests.patch(r_url, headers=headers, data=data, timeout=HTTP_TIMEOUT)
        raise_layman_error(response)
        claimed_username = response.json()['username']
        assert claimed_username == username
