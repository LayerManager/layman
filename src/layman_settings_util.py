import os
from urllib import parse


def read_clients_dict_from_env():
    client_dicts = [
        {
            'id': os.getenv('OAUTH2_CLIENT_ID', ''),
            'secret': os.getenv('OAUTH2_CLIENT_SECRET', None),
        },
    ]
    idx = 1
    while f"OAUTH2_CLIENT{idx}_ID" in os.environ:
        client_dicts.append({
            'id': os.environ[f"OAUTH2_CLIENT{idx}_ID"],
            'secret': os.getenv(f"OAUTH2_CLIENT{idx}_SECRET", None),
        })
        idx += 1
    return client_dicts


def validate_layman_role_service_uri(layman_role_service_uri_str, env_name):
    uri = parse.urlparse(layman_role_service_uri_str)
    exp_uri_schemes = {'postgresql'}
    assert uri.scheme in exp_uri_schemes, \
        f"{env_name} must have one of URL schemes {exp_uri_schemes}, but '{uri.scheme}' was found."

    assert uri.hostname, f"{env_name} must have explicit `host` part."

    query = parse.parse_qs(uri.query)
    schema = query.pop('schema', [None])[0]
    assert schema, f"{env_name} must have query parameter `schema`."
