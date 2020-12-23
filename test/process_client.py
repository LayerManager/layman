import time
import requests
import os
import logging
from functools import partial
from collections import namedtuple

from layman import settings, app
from layman.util import url_for
from layman.layer.geoserver import wfs, wms

logger = logging.getLogger(__name__)

ISS_URL_HEADER = 'AuthorizationIssUrl'
TOKEN_HEADER = 'Authorization'

layer_keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file', 'metadata']
map_keys_to_check = ['thumbnail', 'file', 'metadata']


LAYER_TYPE = 'layman.layer'
MAP_TYPE = 'layman.map'


PUBLICATION_TYPES = [
    LAYER_TYPE,
    MAP_TYPE,
]


PublicationTypeDef = namedtuple('PublicationTypeDef', ['url_param_name',
                                                       'post_url',
                                                       'patch_url',
                                                       'get_list_url',
                                                       'get_url',
                                                       'delete_url',
                                                       'delete_multi_url',
                                                       'keys_to_check',
                                                       'source_path'])
PUBLICATION_TYPES_DEF = {MAP_TYPE: PublicationTypeDef('mapname',
                                                      'rest_maps.post',
                                                      'rest_map.patch',
                                                      'rest_maps.get',
                                                      'rest_map.get',
                                                      'rest_map.delete_map',
                                                      'rest_maps.delete',
                                                      map_keys_to_check,
                                                      'sample/layman.map/small_map.json',
                                                      ),
                         LAYER_TYPE: PublicationTypeDef('layername',
                                                        'rest_layers.post',
                                                        'rest_layer.patch',
                                                        'rest_layers.get',
                                                        'rest_layer.get',
                                                        'rest_layer.delete_layer',
                                                        'rest_layers.delete',
                                                        layer_keys_to_check,
                                                        'sample/layman.layer/small_layer.geojson',
                                                        ),
                         }


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


def patch_publication(publication_type,
                      username,
                      name,
                      file_paths=None,
                      headers=None,
                      access_rights=None,
                      title=None,
                      assert_status=True,
                      ):
    headers = headers or {}
    file_paths = file_paths or []
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.patch_url,
                        username=username,
                        **{publication_type_def.url_param_name: name})

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
        if title:
            data['title'] = title

        r = requests.patch(r_url,
                           files=files,
                           headers=headers,
                           data=data)
        if assert_status:
            assert r.status_code == 200, r.text
    finally:
        for fp in files:
            fp[1][1].close()

    with app.app_context():
        url = url_for(publication_type_def.get_url,
                      username=username,
                      **{publication_type_def.url_param_name: name})
    if assert_status:
        wait_for_rest(url, 30, 0.5, publication_type_def.keys_to_check, headers=headers)
    wfs.clear_cache(username)
    wms.clear_cache(username)
    if not assert_status:
        return r
    return name


def ensure_publication(publication_type,
                       username,
                       name,
                       headers=None,
                       access_rights=None,
                       ):
    headers = headers or {}

    r = get_publications(username, headers=headers, assert_status=False)
    publication_obj = next((publication for publication in r.json() if publication['name'] == name), None)
    if r.status_code == 200 and publication_obj:
        patch_needed = False
        if access_rights is not None:
            if 'read' in access_rights and set(access_rights['read'].split(',')) != set(publication_obj['access_rights']['read']):
                patch_needed = True
            if 'write' in access_rights and set(access_rights['write'].split(',')) != set(publication_obj['access_rights']['write']):
                patch_needed = True
        if patch_needed:
            patch_publication(username, name, access_rights=access_rights, headers=headers)
    else:
        publish_publication(publication_type, username, name, access_rights=access_rights, headers=headers)


def publish_publication(publication_type,
                        username,
                        name,
                        file_paths=None,
                        headers=None,
                        access_rights=None,
                        title=None,
                        assert_status=True,
                        ):
    title = title or name
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
    file_paths = file_paths or [publication_type_def.source_path, ]

    with app.app_context():
        r_url = url_for(publication_type_def.post_url, username=username)

    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [('file', (os.path.basename(fp), open(fp, 'rb'))) for fp in file_paths]
        data = {'name': name,
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
        url = url_for(publication_type_def.get_url,
                      username=username,
                      **{publication_type_def.url_param_name: name})
    if assert_status:
        wait_for_rest(url, 30, 0.5, publication_type_def.keys_to_check, headers=headers)
    else:
        return r
    return name


def get_publications(publication_type, workspace, headers=None, assert_status=True,):
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.get_list_url, username=workspace)
    r = requests.get(r_url, headers=headers)
    if assert_status:
        assert r.status_code == 200, r.text
        return r.json()
    else:
        return r


def get_publication(publication_type, username, name, headers=None, assert_status=True,):
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.get_url,
                        username=username,
                        **{publication_type_def.url_param_name: name})
    r = requests.get(r_url, headers=headers)
    if assert_status:
        assert r.status_code == 200, r.text
        return r.json()
    else:
        return r


def finish_delete(username, url, headers, assert_status):
    r = requests.delete(url, headers=headers)
    if assert_status:
        assert r.status_code == 200, r.text
        result = r.json()
    else:
        result = r
    wfs.clear_cache(username)
    wms.clear_cache(username)
    return result


def delete_publication(publication_type, username, name, headers=None, assert_status=True):
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.delete_url,
                        username=username,
                        **{publication_type_def.url_param_name: name})

    return finish_delete(username, r_url, headers, assert_status)


def delete_publications(publication_type, username, headers=None, assert_status=True):
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.delete_multi_url,
                        username=username,
                        )

    return finish_delete(username, r_url, headers, assert_status)


ensure_layer = partial(ensure_publication, LAYER_TYPE)
ensure_map = partial(ensure_publication, MAP_TYPE)
publish_map = partial(publish_publication, MAP_TYPE)
publish_layer = partial(publish_publication, LAYER_TYPE)
patch_map = partial(patch_publication, MAP_TYPE)
patch_layer = partial(patch_publication, LAYER_TYPE)
get_map = partial(get_publication, MAP_TYPE)
get_layer = partial(get_publication, LAYER_TYPE)
get_maps = partial(get_publications, MAP_TYPE)
get_layers = partial(get_publications, LAYER_TYPE)
delete_map = partial(delete_publication, MAP_TYPE)
delete_layer = partial(delete_publication, LAYER_TYPE)
delete_maps = partial(delete_publications, MAP_TYPE)
delete_layers = partial(delete_publications, LAYER_TYPE)


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
    with app.app_context():
        r_url = url_for('rest_current_user.patch')
    data = {
        'username': username,
    }
    r = requests.patch(r_url, headers=headers, data=data)
    r.raise_for_status()
    claimed_username = r.json()['username']
    assert claimed_username == username


def get_current_user(headers=None):
    headers = headers or {}
    with app.app_context():
        r_url = url_for('rest_current_user.get')
    r = requests.get(r_url, headers=headers)
    r.raise_for_status()
    return r.json()


def ensure_reserved_username(username, headers=None):
    headers = headers or {}
    current_user = get_current_user(headers=headers)
    if 'username' not in current_user:
        reserve_username(username, headers=headers)
    else:
        assert current_user['username'] == username


def get_authz_headers(username):
    return {f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': f'Bearer {username}',
            }
