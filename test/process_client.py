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


def publish_layer(username,
                  layername,
                  file_paths=None,
                  headers=None,
                  title=None,
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
        r = requests.post(r_url,
                          files=files,
                          data=data,
                          headers=headers)
        assert r.status_code == 200, r.text
    finally:
        for fp in files:
            fp[1][1].close()

    with app.app_context():
        url = url_for('rest_layer.get', username=username, layername=layername)
    wait_for_rest(url, 20, 0.5, layer_keys_to_check)
    return layername


def patch_layer(username,
                layername,
                file_paths=None,
                headers=None,
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
    wait_for_rest(url, 20, 0.5, layer_keys_to_check)
    wfs.clear_cache(username)
    wms.clear_cache(username)
    return layername


def patch_map(username,
              mapname,
              headers=None,
              ):
    headers = headers or {}

    with app.app_context():
        r_url = url_for('rest_map.patch', username=username, mapname=mapname)

    data = dict()

    r = requests.patch(r_url,
                       headers=headers,
                       data=data)
    assert r.status_code == 200, r.text

    with app.app_context():
        url = url_for('rest_map.get', username=username, mapname=mapname)
    wait_for_rest(url, 20, 0.5, map_keys_to_check)
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


def publish_map(username,
                mapname,
                file_paths=None,
                headers=None,
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
        r = requests.post(r_url,
                          files=files,
                          data=data,
                          headers=headers)
        assert r.status_code == 200, r.text
    finally:
        for fp in files:
            fp[1][1].close()

    with app.app_context():
        url = url_for('rest_map.get', username=username, mapname=mapname)
    wait_for_rest(url, 20, 0.5, map_keys_to_check)
    return mapname


def delete_map(username, mapname, headers=None):
    headers = headers or {}

    with app.app_context():
        r_url = url_for('rest_map.delete_map', username=username, mapname=mapname)

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
