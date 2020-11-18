import time
import requests
import os
import logging

from layman import settings, app
from layman.util import url_for
from layman.layer.geoserver import wfs, wms

logger = logging.getLogger(__name__)

ISS_URL_HEADER = 'AuthorizationIssUrl'
TOKEN_HEADER = 'Authorization'

layer_keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file', 'metadata']
map_keys_to_check = ['thumbnail', 'file', 'metadata']


def wait_for_rest(url, max_attempts, sleeping_time, keys_to_check, headers=None):
    headers = headers or None
    r = requests.get(url, headers=headers)

    attempts = 1
    while not (r.status_code == 200 and all(
            'status' not in r.json()[k] for k in keys_to_check
    )):
        time.sleep(sleeping_time)
        r = requests.get(url, headers=headers)
        attempts += 1
        if attempts > max_attempts:
            logger.error(f"r.status_code={r.status_code}\nrltest={r.text}")
            raise Exception('Max attempts reached!')


def publish_layer(username,
                  layername,
                  file_paths=None,
                  headers=None,
                  access_rights=None,
                  title=None,
                  assert_status=True,
                  ):
    title = title or layername
    headers = headers or {}
    file_paths = file_paths or ['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson']

    with app.app_context():
        r_url = url_for('rest_layers.post', username=username)

    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [('file', (os.path.basename(fp), open(fp, 'rb'))) for fp in file_paths]
        data = {'name': layername,
                'title': title,
                }
        if access_rights and access_rights.get('read'):
            data["access_rights.read"] = access_rights['read']
        if access_rights and access_rights.get('write'):
            data["access_rights.write"] = access_rights['write']
        r = requests.post(r_url,
                          files=files,
                          data=data,
                          headers=headers)
        if assert_status:
            assert r.status_code == 200, r.text

    finally:
        for fp in files:
            fp[1][1].close()

    with app.app_context():
        url = url_for('rest_layer.get', username=username, layername=layername)
    if assert_status:
        wait_for_rest(url, 30, 0.5, layer_keys_to_check, headers=headers)
    else:
        return r
    return layername


def patch_layer(username,
                layername,
                file_paths=None,
                headers=None,
                access_rights=None,
                ):
    headers = headers or {}
    file_paths = file_paths or []

    with app.app_context():
        r_url = url_for('rest_layer.patch', username=username, layername=layername)

    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [('file', (os.path.basename(fp), open(fp, 'rb'))) for fp in file_paths]
        data = dict()
        if access_rights and access_rights.get('read'):
            data["access_rights.read"] = access_rights['read']
        if access_rights and access_rights.get('write'):
            data["access_rights.write"] = access_rights['write']

        r = requests.patch(r_url,
                           files=files,
                           headers=headers,
                           data=data)
        assert r.status_code == 200, r.text
    finally:
        for fp in files:
            fp[1][1].close()

    with app.app_context():
        url = url_for('rest_layer.get', username=username, layername=layername)
    wait_for_rest(url, 30, 0.5, layer_keys_to_check, headers=headers)
    wfs.clear_cache(username)
    wms.clear_cache(username)
    return layername


def patch_map(username,
              mapname,
              headers=None,
              access_rights=None,
              ):
    headers = headers or {}

    with app.app_context():
        r_url = url_for('rest_map.patch', username=username, mapname=mapname)

    data = dict()
    if access_rights and access_rights.get('read'):
        data["access_rights.read"] = access_rights['read']
    if access_rights and access_rights.get('write'):
        data["access_rights.write"] = access_rights['write']

    r = requests.patch(r_url,
                       headers=headers,
                       data=data)
    assert r.status_code == 200, r.text

    with app.app_context():
        url = url_for('rest_map.get', username=username, mapname=mapname)
    wait_for_rest(url, 30, 0.5, map_keys_to_check, headers=headers)
    wfs.clear_cache(username)
    wms.clear_cache(username)
    return mapname


def delete_layer(username, layername, headers=None):
    headers = headers or {}

    with app.app_context():
        r_url = url_for('rest_layer.delete_layer', username=username, layername=layername)
    r = requests.delete(r_url, headers=headers)
    assert r.status_code == 200, r.text
    wfs.clear_cache(username)
    wms.clear_cache(username)


def get_layer(username, layername, headers=None, assert_status=True,):
    headers = headers or {}

    with app.app_context():
        r_url = url_for('rest_layer.get', username=username, layername=layername)
    r = requests.get(r_url, headers=headers)
    if assert_status:
        assert r.status_code == 200, r.text
        return r.json()
    else:
        return r


def publish_map(username,
                mapname,
                file_paths=None,
                headers=None,
                access_rights=None,
                assert_status=True,
                ):
    headers = headers or {}
    file_paths = file_paths or ['sample/layman.map/full.json', ]

    with app.app_context():
        r_url = url_for('rest_maps.post', username=username)

    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [('file', (os.path.basename(fp), open(fp, 'rb'))) for fp in file_paths]
        data = {'name': mapname, }
        if access_rights and access_rights.get('read'):
            data["access_rights.read"] = access_rights['read']
        if access_rights and access_rights.get('write'):
            data["access_rights.write"] = access_rights['write']
        r = requests.post(r_url,
                          files=files,
                          data=data,
                          headers=headers)
        if assert_status:
            assert r.status_code == 200, r.text
    finally:
        for fp in files:
            fp[1][1].close()

    with app.app_context():
        url = url_for('rest_map.get', username=username, mapname=mapname)
    if assert_status:
        wait_for_rest(url, 30, 0.5, map_keys_to_check, headers=headers)
    else:
        return r
    return mapname


def delete_map(username, mapname, headers=None):
    headers = headers or {}

    with app.app_context():
        r_url = url_for('rest_map.delete_map', username=username, mapname=mapname)

    r = requests.delete(r_url, headers=headers)
    assert r.status_code == 200, r.text


def assert_user_layers(username, layernames, headers=None):
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/{username}/layers"
    r = requests.get(r_url, headers=headers)
    assert r.status_code == 200, f"r.status_code={r.status_code}\nr.text={r.text}"
    layman_names = [li['name'] for li in r.json()]
    assert set(layman_names) == set(layernames), f"Layers {layernames} not equal to {r.text}"


def assert_user_maps(username, mapnames, headers=None):
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/{username}/maps"
    r = requests.get(r_url, headers=headers)
    assert r.status_code == 200, f"r.status_code={r.status_code}\nr.text={r.text}"
    layman_names = [li['name'] for li in r.json()]
    assert set(layman_names) == set(mapnames), f"Maps {mapnames} not equal to {r.text}"


def get_map_metadata_comparison(username, mapname, headers=None):
    with app.app_context():
        r_url = url_for('rest_map_metadata_comparison.get', mapname=mapname, username=username)
    r = requests.get(r_url, headers=headers)
    assert r.status_code == 200, f"r.status_code={r.status_code}\nr.text={r.text}"
    return r.json()


def reserve_username(username, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/current-user?adjust_username=true"
    r = requests.patch(r_url, headers=headers)
    assert r.status_code == 200, r.text
    claimed_username = r.json()['username']
    assert claimed_username == username


def get_authz_headers(username):
    return {f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': f'Bearer {username}',
            }
