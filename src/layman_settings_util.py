import os


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
