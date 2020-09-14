from datetime import date
import glob
import json
import os
import urllib
import time
from multiprocessing import Process
import difflib
import requests

import pytest
from flask import url_for

import sys

del sys.modules['layman']

from . import util, MAP_TYPE
from .micka import csw
from .filesystem import uuid as map_uuid
from layman import app, settings, uuid
from layman import celery as celery_util
from layman.util import url_for as url_for_external
from layman.common.micka import util as micka_common_util
from layman.common.metadata import prop_equals_strict, PROPERTIES

TODAY_DATE = date.today().strftime('%Y-%m-%d')

METADATA_PROPERTIES = {
    'abstract',
    'extent',
    'graphic_url',
    'identifier',
    'map_endpoint',
    'map_file_endpoint',
    'operates_on',
    'organisation_name',
    'publication_date',
    'reference_system',
    'revision_date',
    'title',
}

METADATA_PROPERTIES_EQUAL = METADATA_PROPERTIES

num_maps_before_test = 0


def wait_till_ready(username, mapname):
    last_task = util._get_map_task(username, mapname)
    while last_task is not None and not celery_util.is_task_ready(last_task):
        time.sleep(0.1)
        last_task = util._get_map_task(username, mapname)


def check_metadata(client, username, mapname, props_equal, expected_values):
    with app.app_context():
        rest_path = url_for('rest_map_metadata_comparison.get', username=username, mapname=mapname)
        rv = client.get(rest_path)
        assert rv.status_code == 200, rv.get_json()
        resp_json = rv.get_json()
        assert METADATA_PROPERTIES == set(resp_json['metadata_properties'].keys())
        # for k, v in resp_json['metadata_properties'].items():
        #     print(f"'{k}': {json.dumps(list(v['values'].values())[0], indent=2)},")
        for k, v in resp_json['metadata_properties'].items():
            assert v['equal_or_null'] == (
                k in props_equal), f"Metadata property values have unexpected 'equal_or_null' value: {k}: {json.dumps(v, indent=2)}, sources: {json.dumps(resp_json['metadata_sources'], indent=2)}"
            assert v['equal'] == (
                k in props_equal), f"Metadata property values have unexpected 'equal' value: {k}: {json.dumps(v, indent=2)}, sources: {json.dumps(resp_json['metadata_sources'], indent=2)}"
            # print(f"'{k}': {json.dumps(list(v['values'].values())[0], indent=2)},")
            if k in expected_values:
                vals = list(v['values'].values())
                vals.append(expected_values[k])
                assert prop_equals_strict(vals, equals_fn=PROPERTIES[k].get('equals_fn',
                                                                            None)), f"Property {k} has unexpected values {json.dumps(vals, indent=2)}"


@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    # print('before Process(target=app.run, kwargs={...')
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': settings.LAYMAN_SERVER_NAME.split(':')[1],
        'debug': False,
    })
    # print('before server.start()')
    server.start()
    time.sleep(1)

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    # print('before app.app_context()')
    with app.app_context() as ctx:
        publs_by_type = uuid.check_redis_consistency()
        global num_maps_before_test
        num_maps_before_test = len(publs_by_type[MAP_TYPE])
    yield client

    # print('before server.terminate()')
    server.terminate()
    # print('before server.join()')
    server.join()


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.mark.usefixtures('app_context')
def test_get_maps_empty(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_maps.get', username=username))
    resp_json = rv.get_json()
    assert rv.status_code == 200
    assert len(resp_json) == 0
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': num_maps_before_test + 0
    })


@pytest.mark.usefixtures('app_context')
def test_wrong_value_of_mapname(client):
    username = 'testuser1'
    mapnames = [' ', '2a', 'ě', ';', '?', 'ABC']
    for mapname in mapnames:
        rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
        resp_json = rv.get_json()
        # print('username', username)
        # print(resp_json)
        assert rv.status_code == 400
        assert resp_json['code'] == 2
        assert resp_json['detail']['parameter'] == 'mapname'


@pytest.mark.usefixtures('app_context')
def test_no_file(client):
    rv = client.post(url_for('rest_maps.post', username='testuser1'))
    assert rv.status_code == 400
    resp_json = rv.get_json()
    # print('resp_json', resp_json)
    assert resp_json['code'] == 1
    assert resp_json['detail']['parameter'] == 'file'


@pytest.mark.usefixtures('app_context')
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


@pytest.mark.usefixtures('app_context')
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
        f'{MAP_TYPE}': num_maps_before_test + 0
    })


def test_post_maps_simple(client):
    with app.app_context():
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
            f'{MAP_TYPE}': num_maps_before_test + 1
        })

    with app.app_context():
        rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
        assert rv.status_code == 200
        resp_json = rv.get_json()
        assert resp_json['name'] == mapname
        assert resp_json['uuid'] == uuid_str
        assert resp_json['url'] == url_for_external('rest_map.get', username=username, mapname=mapname)
        assert resp_json['title'] == "Administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
        assert resp_json[
            'description'] == "Na tematick\u00e9 map\u011b p\u0159i p\u0159ibl\u00ed\u017een\u00ed jsou postupn\u011b zobrazovan\u00e9 administrativn\u00ed celky Libereck\u00e9ho kraje : okresy, OP\u00da, ORP a obce."
        map_file = resp_json['file']
        assert 'status' not in map_file
        assert 'path' in map_file
        assert map_file['url'] == url_for_external('rest_map_file.get', username=username, mapname=mapname)
        thumbnail = resp_json['thumbnail']
        assert 'status' in thumbnail
        assert thumbnail['status'] in ['PENDING', 'STARTED']

    with app.app_context():
        map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_map.get', username=username,
                                          mapname=mapname)).get_json()

    with app.app_context():
        rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
        assert rv.status_code == 200
        resp_json = rv.get_json()
        thumbnail = resp_json['thumbnail']
        assert 'status' not in thumbnail
        assert 'path' in thumbnail
        assert thumbnail['url'] == url_for_external('rest_map_thumbnail.get', username=username, mapname=mapname)

    with app.app_context():
        rv = client.get(url_for('rest_map_file.get', username=username, mapname=mapname))
        assert rv.status_code == 200
        resp_json = rv.get_json()
        assert resp_json['name'] == mapname

    with app.app_context():
        map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['metadata'] and map_info['metadata']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_map.get', username=username,
                                          mapname=mapname)).get_json()

    assert set(map_info['metadata'].keys()) == {'identifier', 'csw_url', 'record_url', 'comparison_url'}
    assert map_info['metadata']['identifier'] == f"m-{uuid_str}"
    assert map_info['metadata']['csw_url'] == settings.CSW_PROXY_URL
    md_record_url = f"http://micka:80/record/basic/m-{uuid_str}"
    assert map_info['metadata']['record_url'].replace("http://localhost:3080", "http://micka:80") == md_record_url
    r = requests.get(md_record_url, auth=settings.CSW_BASIC_AUTHN)
    r.raise_for_status()
    assert mapname in r.text

    expected_md_values = {
        'abstract': "Na tematick\u00e9 map\u011b p\u0159i p\u0159ibl\u00ed\u017een\u00ed jsou postupn\u011b zobrazovan\u00e9 administrativn\u00ed celky Libereck\u00e9ho kraje : okresy, OP\u00da, ORP a obce.",
        'extent': [
            14.62,
            50.58,
            15.42,
            50.82
        ],
        'graphic_url': "http://layman_test_run_1:8000/rest/testuser1/maps/administrativni_cleneni_libereckeho_kraje/thumbnail",
        'identifier': {
            "identifier": "http://layman_test_run_1:8000/rest/testuser1/maps/administrativni_cleneni_libereckeho_kraje",
            "label": "administrativni_cleneni_libereckeho_kraje"
        },
        'map_endpoint': "http://layman_test_run_1:8000/rest/testuser1/maps/administrativni_cleneni_libereckeho_kraje",
        'map_file_endpoint': "http://layman_test_run_1:8000/rest/testuser1/maps/administrativni_cleneni_libereckeho_kraje/file",
        'operates_on': [],
        'organisation_name': None,
        'publication_date': TODAY_DATE,
        'reference_system': [
            3857
        ],
        'revision_date': None,
        'title': "Administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje",
    }
    check_metadata(client, username, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)


def test_post_maps_complex(client):
    with app.app_context():
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
            f'{MAP_TYPE}': num_maps_before_test + 2
        })

    with app.app_context():
        rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
        assert rv.status_code == 200
        resp_json = rv.get_json()
        assert resp_json['name'] == mapname
        assert resp_json['uuid'] == uuid_str
        assert resp_json['url'] == url_for_external('rest_map.get', username=username, mapname=mapname)
        assert resp_json['title'] == title
        assert resp_json['description'] == description
        map_file = resp_json['file']
        assert 'status' not in map_file
        assert 'path' in map_file
        assert map_file['url'] == url_for_external('rest_map_file.get', username=username, mapname=mapname)
        thumbnail = resp_json['thumbnail']
        assert 'status' in thumbnail
        assert thumbnail['status'] in ['PENDING', 'STARTED']

    with app.app_context():
        # assert another PATCH is not possible now
        rv = client.patch(url_for('rest_map.patch', username=username, mapname=mapname), data={
            'title': 'abcd',
        })
        assert rv.status_code == 400
        resp_json = rv.get_json()
        assert resp_json['code'] == 29

    # continue with thumbnail assertion
    with app.app_context():
        map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_map.get', username=username,
                                          mapname=mapname)).get_json()

    with app.app_context():
        rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
        assert rv.status_code == 200
        resp_json = rv.get_json()
        thumbnail = resp_json['thumbnail']
        assert 'status' not in thumbnail
        assert 'path' in thumbnail
        assert thumbnail['url'] == url_for_external('rest_map_thumbnail.get', username=username, mapname=mapname)

    with app.app_context():
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

    # continue with metadata assertion
    with app.app_context():
        map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['metadata'] and map_info['metadata']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_map.get', username=username,
                                          mapname=mapname)).get_json()

    expected_md_values = {
        'abstract': "Libovoln\u00fd popis",
        'extent': [
            14.62,
            50.58,
            15.42,
            50.82
        ],
        'graphic_url': "http://layman_test_run_1:8000/rest/testuser1/maps/libe/thumbnail",
        'identifier': {
            "identifier": "http://layman_test_run_1:8000/rest/testuser1/maps/libe",
            "label": "libe"
        },
        'map_endpoint': "http://layman_test_run_1:8000/rest/testuser1/maps/libe",
        'map_file_endpoint': "http://layman_test_run_1:8000/rest/testuser1/maps/libe/file",
        'operates_on': [],
        'organisation_name': None,
        'publication_date': TODAY_DATE,
        'reference_system': [
            3857
        ],
        'revision_date': None,
        'title': "Libereck\u00fd kraj: Administrativn\u00ed \u010dlen\u011bn\u00ed",
    }
    check_metadata(client, username, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)


def test_patch_map(client):
    with app.app_context():
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
            f'{MAP_TYPE}': num_maps_before_test + 2
        })

        assert resp_json['uuid'] == uuid_str
        assert resp_json['url'] == url_for_external('rest_map.get', username=username, mapname=mapname)
        assert resp_json['title'] == "Jiné administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
        assert resp_json['description'] == "Jiný popis"
        map_file = resp_json['file']
        assert 'status' not in map_file
        assert 'path' in map_file
        assert map_file['url'] == url_for_external('rest_map_file.get', username=username, mapname=mapname)
        thumbnail = resp_json['thumbnail']
        assert 'status' in thumbnail
        assert thumbnail['status'] in ['PENDING', 'STARTED']

    with app.app_context():
        map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_map.get', username=username,
                                          mapname=mapname)).get_json()

    with app.app_context():
        rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
        assert rv.status_code == 200
        resp_json = rv.get_json()
        thumbnail = resp_json['thumbnail']
        assert 'status' not in thumbnail
        assert 'path' in thumbnail
        assert thumbnail['url'] == url_for_external('rest_map_thumbnail.get', username=username, mapname=mapname)

    with app.app_context():
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

    with app.app_context():
        map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['metadata'] and map_info['metadata']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_map.get', username=username,
                                          mapname=mapname)).get_json()

    with app.app_context():
        title = 'Nový název'
        rv = client.patch(rest_path, data={
            'title': title,
        })
        assert rv.status_code == 200, rv.get_json()
        resp_json = rv.get_json()
        assert resp_json['title'] == "Nový název"
        assert resp_json['description'] == "Jiný popis"

    with app.app_context():
        description = 'Nový popis'
        rv = client.patch(rest_path, data={
            'description': description,
        })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        assert resp_json['title'] == "Nový název"
        assert resp_json['description'] == "Nový popis"

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': num_maps_before_test + 2
        })

    expected_md_values = {
        'abstract': "Nov\u00fd popis",
        'extent': [
            14.623,
            50.58,
            15.42,
            50.82
        ],
        'graphic_url': "http://layman_test_run_1:8000/rest/testuser1/maps/administrativni_cleneni_libereckeho_kraje/thumbnail",
        'identifier': {
            "identifier": "http://layman_test_run_1:8000/rest/testuser1/maps/administrativni_cleneni_libereckeho_kraje",
            "label": "administrativni_cleneni_libereckeho_kraje"
        },
        'map_endpoint': "http://layman_test_run_1:8000/rest/testuser1/maps/administrativni_cleneni_libereckeho_kraje",
        'map_file_endpoint': "http://layman_test_run_1:8000/rest/testuser1/maps/administrativni_cleneni_libereckeho_kraje/file",
        'operates_on': [],
        'organisation_name': None,
        'publication_date': TODAY_DATE,
        'reference_system': [
            3857
        ],
        'revision_date': TODAY_DATE,
        'title': "Nov\u00fd n\u00e1zev",
    }
    check_metadata(client, username, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)


def test_delete_map(client):
    with app.app_context():
        username = 'testuser1'
        mapname = 'administrativni_cleneni_libereckeho_kraje'
        rest_path = url_for('rest_map.delete_map', username=username, mapname=mapname)
        rv = client.delete(rest_path)
        assert rv.status_code == 200
        resp_json = rv.get_json()
        uuid_str = resp_json['uuid']
        md_record_url = f"http://micka:80/record/basic/m-{uuid_str}"
        r = requests.get(md_record_url, auth=settings.CSW_BASIC_AUTHN)
        r.raise_for_status()
        assert 'Záznam nenalezen' in r.text
        assert mapname not in r.text

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': num_maps_before_test + 1
        })

    with app.app_context():
        rest_path = url_for('rest_map.delete_map', username=username, mapname=mapname)
        rv = client.delete(rest_path)
        assert rv.status_code == 404
        resp_json = rv.get_json()
        assert resp_json['code'] == 26

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': num_maps_before_test + 1
        })


def test_map_composed_from_local_layers(client):
    with app.app_context():
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
            layer1uuid = rv.get_json()[0]['uuid']
        finally:
            for fp in files:
                fp[0].close()

    # TODO if no sleep, Micka throws 500
    # [2020-03-26 09-54-11] Dibi\UniqueConstraintViolationException: duplicate key value violates unique constraint "edit_md_pkey" DETAIL:  Key (recno)=(17) already exists. SCHEMA NAME:  public TABLE NAME:  edit_md CONSTRAINT NAME:  edit_md_pkey LOCATION:  _bt_check_unique, nbtinsert.c:434 #23505 in /var/www/html/Micka/php/vendor/dibi/dibi/src/Dibi/Drivers/PostgreDriver.php:150  @  http://localhost:3080/csw  @@  exception--2020-03-26--09-54--3f034f5a61.html
    # in /var/www/html/Micka/php/app/model/RecordModel.php, line 197 setEditMd2Md INSERT INTO ...
    # probably problem with concurrent CSW insert
    # so report bug to Micka
    time.sleep(0.3)

    with app.app_context():
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
            layer2uuid = rv.get_json()[0]['uuid']
        finally:
            for fp in files:
                fp[0].close()

    with app.app_context():
        keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'metadata']
        layer_info = client.get(url_for('rest_layer.get', username=username, layername=layername1)).get_json()
        max_attempts = 100
        num_attempts = 1
    while num_attempts < max_attempts and any(('status' in layer_info[key] for key in keys_to_check)):
        time.sleep(0.1)
        # print('layer_info1', layer_info)
        with app.app_context():
            layer_info = client.get(url_for('rest_layer.get', username=username, layername=layername1)).get_json()
        num_attempts += 1
    assert num_attempts < max_attempts, f"Max attempts reached, layer1info={layer_info}"
    wms_url1 = layer_info['wms']['url']

    with app.app_context():
        layer_info = client.get(url_for('rest_layer.get', username=username, layername=layername2)).get_json()
        num_attempts = 1
    while any(('status' in layer_info[key] for key in keys_to_check)):
        time.sleep(0.1)
        # print('layer_info2', layer_info)
        with app.app_context():
            layer_info = client.get(url_for('rest_layer.get', username=username, layername=layername2)).get_json()
        num_attempts += 1
    assert num_attempts < max_attempts, f"Max attempts reached, layer2info={layer_info}"
    wms_url2 = layer_info['wms']['url']

    expected_url = 'http://localhost:8000/geoserver/testuser1/ows'
    assert wms_url1 == expected_url
    assert wms_url2 == expected_url

    with app.app_context():
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

    with app.app_context():
        map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
        thumbnail = map_info['thumbnail']
        assert 'status' in thumbnail
        assert thumbnail['status'] in ['PENDING', 'STARTED']

    with app.app_context():
        map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_map.get', username=username,
                                          mapname=mapname)).get_json()

    with app.app_context():
        rv = client.get(url_for('rest_map.get', username=username, mapname=mapname))
        assert rv.status_code == 200
        resp_json = rv.get_json()
        thumbnail = resp_json['thumbnail']
        assert 'status' not in thumbnail
        assert 'path' in thumbnail
        assert thumbnail['url'] == url_for_external('rest_map_thumbnail.get', username=username, mapname=mapname)

        # uuid.check_redis_consistency(expected_publ_num_by_type={
        #     f'{MAP_TYPE}': num_maps_before_test + 2
        # })

    with app.app_context():
        map_info = client.get(url_for('rest_map.get', username=username, mapname=mapname)).get_json()
    while 'status' in map_info['metadata'] and map_info['metadata']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_map.get', username=username,
                                          mapname=mapname)).get_json()

    with app.app_context():
        # assert metadata file is the same as filled template except for UUID and dates
        template_path, prop_values = csw.get_template_path_and_values(username, mapname, http_method='post')
        xml_file_object = micka_common_util.fill_xml_template_as_pretty_file_object(template_path, prop_values,
                                                                                    csw.METADATA_PROPERTIES)
        expected_path = 'src/layman/map/rest_test_filled_template.xml'
        with open(expected_path) as f:
            expected_lines = f.readlines()
        diff_lines = list(
            difflib.unified_diff([line.decode('utf-8') for line in xml_file_object.readlines()], expected_lines))
        assert len(diff_lines) == 40, ''.join(diff_lines)
        plus_lines = [line for line in diff_lines if line.startswith('+ ')]
        assert len(plus_lines) == 5
        minus_lines = [line for line in diff_lines if line.startswith('- ')]
        assert len(minus_lines) == 5

        plus_line = plus_lines[0]
        assert plus_line == '+    <gco:CharacterString>m-91147a27-1ff4-4242-ba6d-faffb92224c6</gco:CharacterString>\n'
        minus_line = minus_lines[0]
        assert minus_line.startswith('-    <gco:CharacterString>m') and minus_line.endswith('</gco:CharacterString>\n')

        plus_line = plus_lines[1]
        assert plus_line == '+    <gco:Date>2007-05-25</gco:Date>\n'
        minus_line = minus_lines[1]
        assert minus_line.startswith('-    <gco:Date>') and minus_line.endswith('</gco:Date>\n')

        plus_line = plus_lines[2]
        assert plus_line == '+                <gco:Date>2007-05-25</gco:Date>\n'
        minus_line = minus_lines[2]
        assert minus_line.startswith('-                <gco:Date>') and minus_line.endswith('</gco:Date>\n')

        plus_line = plus_lines[3]
        assert plus_line.startswith(
            '+      <srv:operatesOn xlink:href="http://localhost:3080/csw?SERVICE=CSW&amp;VERSION=2.0.2&amp;REQUEST=GetRecordById&amp;OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&amp;ID=') and plus_line.endswith(
            '" xlink:title="hranice" xlink:type="simple"/>\n'), plus_line
        minus_line = minus_lines[3]
        assert minus_line.startswith(
            '-      <srv:operatesOn xlink:href="http://localhost:3080/csw?SERVICE=CSW&amp;VERSION=2.0.2&amp;REQUEST=GetRecordById&amp;OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&amp;ID=') and minus_line.endswith(
            '" xlink:title="hranice" xlink:type="simple"/>\n'), minus_line

        plus_line = plus_lines[4]
        assert plus_line.startswith(
            '+      <srv:operatesOn xlink:href="http://localhost:3080/csw?SERVICE=CSW&amp;VERSION=2.0.2&amp;REQUEST=GetRecordById&amp;OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&amp;ID=') and plus_line.endswith(
            '" xlink:title="mista" xlink:type="simple"/>\n'), plus_line
        minus_line = minus_lines[4]
        assert minus_line.startswith(
            '-      <srv:operatesOn xlink:href="http://localhost:3080/csw?SERVICE=CSW&amp;VERSION=2.0.2&amp;REQUEST=GetRecordById&amp;OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&amp;ID=') and minus_line.endswith(
            '" xlink:title="mista" xlink:type="simple"/>\n'), minus_line

    expected_md_values = {
        'abstract': "World places and boundaries abstract",
        'extent': [
            -35.0,
            -48.5,
            179.0,
            81.5
        ],
        'graphic_url': "http://layman_test_run_1:8000/rest/testuser1/maps/svet/thumbnail",
        'identifier': {
            "identifier": "http://layman_test_run_1:8000/rest/testuser1/maps/svet",
            "label": "svet"
        },
        'map_endpoint': "http://layman_test_run_1:8000/rest/testuser1/maps/svet",
        'map_file_endpoint': "http://layman_test_run_1:8000/rest/testuser1/maps/svet/file",
        'operates_on': [
            {
                "xlink:href": f"http://localhost:3080/csw?SERVICE=CSW&VERSION=2.0.2&REQUEST=GetRecordById&OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&ID=m-{layer2uuid}#_m-{layer2uuid}",
                "xlink:title": "hranice"
            },
            {
                "xlink:href": f"http://localhost:3080/csw?SERVICE=CSW&VERSION=2.0.2&REQUEST=GetRecordById&OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&ID=m-{layer1uuid}#_m-{layer1uuid}",
                "xlink:title": "mista"
            }
        ],
        'organisation_name': None,
        'publication_date': TODAY_DATE,
        'reference_system': [
            3857
        ],
        'revision_date': None,
        'title': "World places and boundaries",
    }
    check_metadata(client, username, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)
