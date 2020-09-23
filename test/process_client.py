import requests
import os
import time

from layman import settings

ISS_URL_HEADER = 'AuthorizationIssUrl'
TOKEN_HEADER = 'Authorization'

layer_keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file', 'metadata']


def wait_for_rest(url, max_attempts, sleeping_time, keys_to_check):
    r = requests.get(url)

    attempts = 1
    while not (r.status_code == 200 and all(
            'status' not in r.json()[k] for k in keys_to_check
    )):
        time.sleep(sleeping_time)
        r = requests.get(url)
        attempts += 1
        if attempts > max_attempts:
            raise Exception('Max attempts reached!')


def publish_layer(username, layername, file_paths, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"

    r_url = f"{rest_url}/{username}/layers"
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        r = requests.post(r_url,
                          files=[('file', (os.path.basename(fp), open(fp, 'rb'))) for fp in file_paths],
                          data={'name': layername, },
                          headers=headers)
        assert r.status_code == 200, r.text
    finally:
        for fp in files:
            fp[0].close()

    wait_for_rest(f"{rest_url}/{username}/layers/{layername}", 20, 0.5, layer_keys_to_check)
    return layername


def patch_layer(username, layername, file_paths, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"

    r_url = f"{rest_url}/{username}/layers/{layername}"
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        r = requests.patch(r_url, files=[
            ('file', (os.path.basename(fp), open(fp, 'rb')))
            for fp in file_paths
        ], headers=headers)
        assert r.status_code == 200, r.text
    finally:
        for fp in files:
            fp[0].close()

    wait_for_rest(f"{rest_url}/{username}/layers/{layername}", 20, 0.5, layer_keys_to_check)
    return layername


def delete_layer(username, layername, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"

    r_url = f"{rest_url}/{username}/layers/{layername}"
    r = requests.delete(r_url, headers=headers)
    assert r.status_code == 200, r.text


def assert_user_layers(username, layernames):
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/{username}/layers"
    r = requests.get(r_url)
    assert r.status_code == 200, f"r.status_code={r.status_code}\n{r.text}=r.text"
    layman_names = [li['name'] for li in r.json()]
    assert set(layman_names) == set(layernames), f"{r.text}=r.text"


def reserve_username(username, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/current-user?adjust_username=true"
    r = requests.patch(r_url, headers=headers)
    assert r.status_code == 200, r.text
    claimed_username = r.json()['username']
    assert claimed_username == username
