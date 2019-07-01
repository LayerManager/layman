import glob
import os
import urllib
import time
from multiprocessing import Process

import pytest
from flask import url_for

from . import MAP_TYPE
from layman import app
from layman import uuid
from layman.map.filesystem import uuid as map_uuid


PORT = 8000

@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    # print('before Process(target=app.run, kwargs={...')
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': PORT,
        'debug': False,
    })
    # print('before server.start()')
    server.start()
    time.sleep(1)

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = f'layman_test:{PORT}'
    app.config['SESSION_COOKIE_DOMAIN'] = f'layman_test:{PORT}'

    # print('before app.app_context()')
    with app.app_context() as ctx:
        yield client

    # print('before server.terminate()')
    server.terminate()
    # print('before server.join()')
    server.join()


def test_get_maps_empty(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_maps.get', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 0
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 0
    })


def test_no_file(client):
    rv = client.post(url_for('rest_maps.post', username='testuser1'))
    assert rv.status_code==400
    resp_json = rv.get_json()
    # print('resp_json', resp_json)
    assert resp_json['code']==1
    assert resp_json['detail']['parameter']=='file'


def test_post_maps_invalid_file(client):
    username = 'testuser1'
    rest_path = url_for('rest_maps.post', username=username)
    file_paths = [
        'sample/style/generic-blue.xml',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post(rest_path, data={
            'file': files
        })
        assert rv.status_code == 400
        resp_json = rv.get_json()
        # print('resp_json', resp_json)
        assert resp_json['code'] == 2
        assert resp_json['detail']['parameter'] == 'file'
        assert resp_json['detail']['reason'] == 'Invalid JSON syntax'
    finally:
        for fp in files:
            fp[0].close()


def test_post_maps_invalid_json(client):
    username = 'testuser1'
    rest_path = url_for('rest_maps.post', username=username)
    file_paths = [
        'sample/layman.map/invalid-missing-title-email.json',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post(rest_path, data={
            'file': files
        })
        assert rv.status_code == 400
        resp_json = rv.get_json()
        # print('resp_json', resp_json)
        assert resp_json['code'] == 2
        assert resp_json['detail']['parameter'] == 'file'
        assert resp_json['detail']['reason'] == 'JSON not valid against schema layman/map/schema.draft-07.json'
        assert len(resp_json['detail']['validation-errors']) == 2
    finally:
        for fp in files:
            fp[0].close()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 0
    })


def test_post_maps_simple(client):
    username = 'testuser1'
    mapname = None
    expected_mapname = 'administrativni_cleneni_libereckeho_kraje'
    rest_path = url_for('rest_maps.post', username=username)
    file_paths = [
        'sample/layman.map/full.json',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post(rest_path, data={
            'file': files
        })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        # print('resp_json', resp_json)
        assert len(resp_json) == 1
        assert resp_json[0]['name'] == expected_mapname
        mapname = resp_json[0]['name']
        uuid_str = resp_json[0]['uuid']
    finally:
        for fp in files:
            fp[0].close()

    assert uuid.is_valid_uuid(uuid_str)

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 1
    })

    rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['name'] == mapname
    assert resp_json['uuid'] == uuid_str
    assert resp_json['url'] == urllib.parse.urlparse(url_for('rest_map.get', username=username, mapname=mapname)).path
    assert resp_json['title'] == "Administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
    assert resp_json['description'] == "Na tematick\u00e9 map\u011b p\u0159i p\u0159ibl\u00ed\u017een\u00ed jsou postupn\u011b zobrazovan\u00e9 administrativn\u00ed celky Libereck\u00e9ho kraje : okresy, OP\u00da, ORP a obce."
    map_file = resp_json['file']
    assert 'status' not in map_file
    assert 'path' in map_file
    assert map_file['url'] == urllib.parse.urlparse(url_for('rest_map_file.get', username=username, mapname=mapname)).path
    thumbnail = resp_json['thumbnail']
    assert 'status' in thumbnail
    assert thumbnail['status'] == 'PENDING'

    map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] == 'PENDING':
        time.sleep(0.1)
        map_info = client.get(url_for('rest_map.get', username=username,
                                      mapname=mapname)).get_json()

    rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
    assert rv.status_code == 200
    resp_json = rv.get_json()
    thumbnail = resp_json['thumbnail']
    assert 'status' not in thumbnail
    assert 'path' in thumbnail
    assert thumbnail['url'] == urllib.parse.urlparse(url_for('rest_map_thumbnail.get', username=username, mapname=mapname)).path

    rv = client.get(url_for('rest_map_file.get', username=username, mapname=mapname))
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['name'] == mapname


def test_post_maps_complex(client):
    username = 'testuser1'
    mapname = 'libe'
    title = 'Liberecký kraj: Administrativní členění'
    description = 'Libovolný popis'
    rest_path = url_for('rest_maps.post', username=username)
    file_paths = [
        'sample/layman.map/full.json',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post(rest_path, data={
            'file': files,
            'name': mapname,
            'title': title,
            'description': description,
        })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        # print('resp_json', resp_json)
        assert len(resp_json) == 1
        assert resp_json[0]['name'] == mapname
        uuid_str = resp_json[0]['uuid']
    finally:
        for fp in files:
            fp[0].close()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 2
    })

    rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['name'] == mapname
    assert resp_json['uuid'] == uuid_str
    assert resp_json['url'] == urllib.parse.urlparse(url_for('rest_map.get', username=username, mapname=mapname)).path
    assert resp_json['title'] == title
    assert resp_json['description'] == description
    map_file = resp_json['file']
    assert 'status' not in map_file
    assert 'path' in map_file
    assert map_file['url'] == urllib.parse.urlparse(url_for('rest_map_file.get', username=username, mapname=mapname)).path
    thumbnail = resp_json['thumbnail']
    assert 'status' in thumbnail
    assert thumbnail['status'] == 'PENDING'

    # assert another PATCH is not possible now
    rv = client.patch(url_for('rest_map.patch', username=username, mapname=mapname), data={
        'title': 'abcd',
    })
    assert rv.status_code == 400
    resp_json = rv.get_json()
    assert resp_json['code']==29

    # continue with thumbnail assertion
    map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] == 'PENDING':
        time.sleep(0.1)
        map_info = client.get(url_for('rest_map.get', username=username,
                                      mapname=mapname)).get_json()

    rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
    assert rv.status_code == 200
    resp_json = rv.get_json()
    thumbnail = resp_json['thumbnail']
    assert 'status' not in thumbnail
    assert 'path' in thumbnail
    assert thumbnail['url'] == urllib.parse.urlparse(url_for('rest_map_thumbnail.get', username=username, mapname=mapname)).path

    rv = client.get(url_for('rest_map_file.get', username=username, mapname=mapname))
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['name'] == mapname
    assert resp_json['title'] == title
    assert resp_json['abstract'] == description
    user_json = resp_json['user']
    assert user_json['name'] == username
    assert user_json['email'] == ''
    assert len(user_json) == 2
    groups_json = resp_json['groups']
    assert groups_json['guest'] == 'w'
    assert len(groups_json) == 1


def test_patch_map(client):
    username = 'testuser1'
    mapname = 'administrativni_cleneni_libereckeho_kraje'
    uuid_str = map_uuid.get_map_uuid(username, mapname)
    rest_path = url_for('rest_map.patch', username=username, mapname=mapname)

    file_paths = [
        'sample/layman.map/full2.json',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.patch(rest_path, data={
            'file': files,
        })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        # print('resp_json', resp_json)
    finally:
        for fp in files:
            fp[0].close()

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 2
    })

    assert resp_json['uuid'] == uuid_str
    assert resp_json['url'] == urllib.parse.urlparse(url_for('rest_map.get', username=username, mapname=mapname)).path
    assert resp_json['title'] == "Jiné administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
    assert resp_json['description'] == "Jiný popis"
    map_file = resp_json['file']
    assert 'status' not in map_file
    assert 'path' in map_file
    assert map_file['url'] == urllib.parse.urlparse(url_for('rest_map_file.get', username=username, mapname=mapname)).path
    thumbnail = resp_json['thumbnail']
    assert 'status' in thumbnail
    assert thumbnail['status'] == 'PENDING'

    map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] == 'PENDING':
        time.sleep(0.1)
        map_info = client.get(url_for('rest_map.get', username=username,
                                      mapname=mapname)).get_json()

    rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
    assert rv.status_code == 200
    resp_json = rv.get_json()
    thumbnail = resp_json['thumbnail']
    assert 'status' not in thumbnail
    assert 'path' in thumbnail
    assert thumbnail['url'] == urllib.parse.urlparse(url_for('rest_map_thumbnail.get', username=username, mapname=mapname)).path

    rv = client.get(url_for('rest_map_file.get', username=username, mapname=mapname))
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['name'] == mapname
    assert resp_json['title'] == "Jiné administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
    assert resp_json['abstract'] == "Jiný popis"
    user_json = resp_json['user']
    assert user_json['name'] == username
    assert user_json['email'] == ''
    assert len(user_json) == 2
    groups_json = resp_json['groups']
    assert groups_json['guest'] == 'w'
    assert len(groups_json) == 1

    title = 'Nový název'
    rv = client.patch(rest_path, data={
        'title': title,
    })
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['title'] == "Nový název"
    assert resp_json['description'] == "Jiný popis"

    description = 'Nový popis'
    rv = client.patch(rest_path, data={
        'description': description,
    })
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['title'] == "Nový název"
    assert resp_json['description'] == "Nový popis"

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 2
    })


def test_delete_map(client):
    username = 'testuser1'
    mapname = 'administrativni_cleneni_libereckeho_kraje'
    rest_path = url_for('rest_map.delete_map', username=username, mapname=mapname)
    rv = client.delete(rest_path)
    assert rv.status_code == 200

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 1
    })

    rest_path = url_for('rest_map.delete_map', username=username, mapname=mapname)
    rv = client.delete(rest_path)
    assert rv.status_code == 404
    resp_json = rv.get_json()
    assert resp_json['code'] == 26

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 1
    })


def test_map_composed_from_local_layers(client):
    username = 'testuser1'
    rest_path = url_for('rest_layers.post', username=username)

    layername1 = 'mista'
    pattern = os.path.join(os.getcwd(), 'tmp/naturalearth/110m/cultural/ne_110m_populated_places.*')
    file_paths = glob.glob(pattern)
    assert len(file_paths) > 0
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post(rest_path, data={
            'file': files,
            'name': layername1,
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    layername2 = 'hranice'
    pattern = os.path.join(os.getcwd(), 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.*')
    file_paths = glob.glob(pattern)
    assert len(file_paths) > 0
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post(rest_path, data={
            'file': files,
            'name': layername2,
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail']
    layer_info = client.get(url_for('rest_layer.get', username=username, layername=layername1)).get_json()
    while any(('status' in layer_info[key] for key in keys_to_check)):
        time.sleep(0.1)
        print('layer_info1', layer_info)
        layer_info = client.get(url_for('rest_layer.get', username=username, layername=layername1)).get_json()
    wms_url1 = layer_info['wms']['url']

    layer_info = client.get(url_for('rest_layer.get', username=username, layername=layername2)).get_json()
    while any(('status' in layer_info[key] for key in keys_to_check)):
        time.sleep(0.1)
        print('layer_info2', layer_info)
        layer_info = client.get(url_for('rest_layer.get', username=username, layername=layername2)).get_json()
    wms_url2 = layer_info['wms']['url']

    expected_url = 'http://localhost:8600/geoserver/testuser1/ows'
    assert wms_url1 == expected_url
    assert wms_url2 == expected_url

    mapname = 'svet'
    rest_path = url_for('rest_maps.post', username=username)
    file_paths = [
        'sample/layman.map/internal_url.json',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post(rest_path, data={
            'file': files,
            'name': mapname,
        })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        # print('resp_json', resp_json)
        assert len(resp_json) == 1
        assert resp_json[0]['name'] == mapname
    finally:
        for fp in files:
            fp[0].close()

    map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    thumbnail = map_info['thumbnail']
    assert 'status' in thumbnail
    assert thumbnail['status'] == 'PENDING'

    map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] == 'PENDING':
        time.sleep(0.1)
        map_info = client.get(url_for('rest_map.get', username=username,
                                      mapname=mapname)).get_json()

    rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
    assert rv.status_code == 200
    resp_json = rv.get_json()
    thumbnail = resp_json['thumbnail']
    assert 'status' not in thumbnail
    assert 'path' in thumbnail
    assert thumbnail['url'] == urllib.parse.urlparse(url_for('rest_map_thumbnail.get', username=username, mapname=mapname)).path
