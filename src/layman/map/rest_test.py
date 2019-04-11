import os

import pytest
from flask import url_for

from . import MAP_TYPE
from layman import app as layman
from layman import uuid


@pytest.fixture
def client():
    layman.config['TESTING'] = True
    layman.config['SERVER_NAME'] = '127.0.0.1:9000'
    layman.config['SESSION_COOKIE_DOMAIN'] = 'localhost:9000'
    client = layman.test_client()

    with layman.app_context() as ctx:
        ctx.push()
        pass

    yield client

def test_get_maps_empty(client):
    username = 'testuser1'
    with layman.app_context():
        rv = client.get(url_for('rest_maps.get', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 0
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 0
    })


def test_no_file(client):
    with layman.app_context():
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
        with layman.app_context():
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
        with layman.app_context():
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
        with layman.app_context():
            rv = client.post(rest_path, data={
                'file': files
            })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        # print('resp_json', resp_json)
        assert len(resp_json) == 1
        assert resp_json[0]['name'] == expected_mapname
        mapname = resp_json[0]['name']
    finally:
        for fp in files:
            fp[0].close()

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 1
    })

    with layman.app_context():
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
        with layman.app_context():
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
    finally:
        for fp in files:
            fp[0].close()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': 2
    })

    with layman.app_context():
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


