from contextlib import ExitStack
from datetime import date
import glob
import json
import os
import time
import difflib
import sys
import requests
import pytest

del sys.modules['layman']

from layman import app, settings, uuid, celery as celery_util
from layman.common.micka import util as micka_common_util
from layman.common.metadata import prop_equals_strict, PROPERTIES
from layman.util import SimpleCounter
from test_tools import flask_client
from test_tools.util import url_for, url_for_external
from . import util, MAP_TYPE
from .micka import csw
from .filesystem import uuid as map_uuid

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

publication_counter = SimpleCounter()


def wait_till_ready(workspace, mapname):
    chain_info = util.get_map_chain(workspace, mapname)
    while chain_info is not None and not celery_util.is_chain_ready(chain_info):
        time.sleep(0.1)
        chain_info = util.get_map_chain(workspace, mapname)


def check_metadata(client, workspace, mapname, props_equal, expected_values):
    with app.app_context():
        rest_path = url_for('rest_workspace_map_metadata_comparison.get', workspace=workspace, mapname=mapname)
        response = client.get(rest_path)
        assert response.status_code == 200, response.get_json()
        resp_json = response.get_json()
        assert METADATA_PROPERTIES == set(resp_json['metadata_properties'].keys())
        # for k, v in resp_json['metadata_properties'].items():
        #     print(f"'{k}': {json.dumps(list(v['values'].values())[0], indent=2)},")
        for key, value in resp_json['metadata_properties'].items():
            assert value['equal_or_null'] == (
                key in props_equal), f"Metadata property values have unexpected 'equal_or_null' value: {key}: {json.dumps(value, indent=2)}, sources: {json.dumps(resp_json['metadata_sources'], indent=2)}"
            assert value['equal'] == (
                key in props_equal), f"Metadata property values have unexpected 'equal' value: {key}: {json.dumps(value, indent=2)}, sources: {json.dumps(resp_json['metadata_sources'], indent=2)}"
            # print(f"'{k}': {json.dumps(list(v['values'].values())[0], indent=2)},")
            if key in expected_values:
                vals = list(value['values'].values())
                vals.append(expected_values[key])
                assert prop_equals_strict(vals, equals_fn=PROPERTIES[key].get('equals_fn',
                                                                              None)), \
                    f"Property {key} has unexpected values {json.dumps(vals, indent=2)}"


@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    yield client


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.mark.usefixtures('ensure_layman')
def test_get_maps_empty(client):
    workspace = 'testuser1'
    flask_client.ensure_workspace(workspace, client)
    with app.app_context():
        response = client.get(url_for('rest_workspace_maps.get', workspace=workspace))
        resp_json = response.get_json()
        assert response.status_code == 200, response.data
        assert len(resp_json) == 0

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': publication_counter.get()
        })


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_wrong_value_of_mapname(client):
    workspace = 'testuser1'
    mapnames = [' ', 'ě', ';', '?', 'ABC']
    for mapname in mapnames:
        response = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname))
        resp_json = response.get_json()
        # print('workspace', workspace)
        # print(resp_json)
        assert response.status_code == 400
        assert resp_json['code'] == 2
        assert resp_json['detail']['parameter'] == 'mapname'


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_no_file(client):
    response = client.post(url_for('rest_workspace_maps.post', workspace='testuser1'))
    assert response.status_code == 400
    resp_json = response.get_json()
    # print('resp_json', resp_json)
    assert resp_json['code'] == 1
    assert resp_json['detail']['parameter'] == 'file'


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_post_maps_invalid_file(client):
    workspace = 'testuser1'
    rest_path = url_for('rest_workspace_maps.post', workspace=workspace)
    file_paths = [
        'sample/style/generic-blue_sld.xml',
    ]
    for file_path in file_paths:
        assert os.path.isfile(file_path)
    with ExitStack() as stack:
        files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
        response = client.post(rest_path, data={
            'file': files,
        })
    assert response.status_code == 400
    resp_json = response.get_json()
    # print('resp_json', resp_json)
    assert resp_json['code'] == 2
    assert resp_json['detail']['parameter'] == 'file'
    assert resp_json['detail']['reason'] == 'Invalid JSON syntax'


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_post_maps_invalid_json(client):
    workspace = 'testuser1'
    rest_path = url_for('rest_workspace_maps.post', workspace=workspace)
    file_paths = [
        'sample/layman.map/invalid-missing-title-email.json',
    ]
    for file_path in file_paths:
        assert os.path.isfile(file_path)
    with ExitStack() as stack:
        files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
        response = client.post(rest_path, data={
            'file': files,
        })
    assert response.status_code == 400
    resp_json = response.get_json()
    # print('resp_json', resp_json)
    assert resp_json['code'] == 2
    assert resp_json['detail']['parameter'] == 'file'
    assert resp_json['detail']['reason'] == 'JSON not valid against schema https://raw.githubusercontent.com/hslayers/map-compositions/2.0.0/schema.json'
    assert len(resp_json['detail']['validation-errors']) == 2

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('ensure_layman')
def test_post_maps_simple(client):
    with app.app_context():
        workspace = 'testuser1'
        mapname = None
        expected_mapname = 'administrativni_cleneni_libereckeho_kraje'
        rest_path = url_for('rest_workspace_maps.post', workspace=workspace)
        file_paths = [
            'sample/layman.map/full.json',
        ]
        for file_path in file_paths:
            assert os.path.isfile(file_path)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.post(rest_path, data={
                'file': files,
            })
        assert response.status_code == 200
        resp_json = response.get_json()
        # print('resp_json', resp_json)
        assert len(resp_json) == 1
        assert resp_json[0]['name'] == expected_mapname
        mapname = resp_json[0]['name']
        uuid_str = resp_json[0]['uuid']

        assert uuid.is_valid_uuid(uuid_str)

        publication_counter.increase()
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': publication_counter.get()
        })

    with app.app_context():
        response = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname))
        assert response.status_code == 200
        resp_json = response.get_json()
        assert resp_json['name'] == mapname
        assert resp_json['uuid'] == uuid_str
        assert resp_json['url'] == url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname)
        assert resp_json['title'] == "Administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
        assert resp_json[
            'description'] == "Na tematick\u00e9 map\u011b p\u0159i p\u0159ibl\u00ed\u017een\u00ed jsou postupn\u011b zobrazovan\u00e9 administrativn\u00ed celky Libereck\u00e9ho kraje : okresy, OP\u00da, ORP a obce."
        map_file = resp_json['file']
        assert 'status' not in map_file
        assert 'path' in map_file
        assert map_file['url'] == url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname)
        thumbnail = resp_json['thumbnail']
        assert 'status' in thumbnail
        assert thumbnail['status'] in ['PENDING', 'STARTED']
        assert 'id' not in resp_json.keys()
        assert 'type' not in resp_json.keys()

    with app.app_context():
        map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace,
                                          mapname=mapname)).get_json()

    with app.app_context():
        response = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname))
        assert response.status_code == 200
        resp_json = response.get_json()
        thumbnail = resp_json['thumbnail']
        assert 'status' not in thumbnail
        assert 'path' in thumbnail
        assert thumbnail['url'] == url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname)

    with app.app_context():
        response = client.get(url_for('rest_workspace_map_file.get', workspace=workspace, mapname=mapname))
        assert response.status_code == 200
        resp_json = response.get_json()
        assert resp_json['name'] == mapname

    with app.app_context():
        map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)).get_json()
    while 'status' in map_info['metadata'] and map_info['metadata']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace,
                                          mapname=mapname)).get_json()

    assert set(map_info['metadata'].keys()) == {'identifier', 'csw_url', 'record_url', 'comparison_url'}
    assert map_info['metadata']['identifier'] == f"m-{uuid_str}"
    assert map_info['metadata']['csw_url'] == settings.CSW_PROXY_URL
    md_record_url = f"http://micka:80/record/basic/m-{uuid_str}"
    assert map_info['metadata']['record_url'].replace("http://localhost:3080", "http://micka:80") == md_record_url
    response = requests.get(md_record_url, auth=settings.CSW_BASIC_AUTHN, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    response.raise_for_status()
    assert mapname in response.text

    with app.app_context():
        expected_md_values = {
            'abstract': "Na tematick\u00e9 map\u011b p\u0159i p\u0159ibl\u00ed\u017een\u00ed jsou postupn\u011b zobrazovan\u00e9 administrativn\u00ed celky Libereck\u00e9ho kraje : okresy, OP\u00da, ORP a obce.",
            'extent': [
                14.62,
                50.58,
                15.42,
                50.82
            ],
            'graphic_url': url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname),
            'identifier': {
                "identifier": url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
                "label": "administrativni_cleneni_libereckeho_kraje"
            },
            'map_endpoint': url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
            'map_file_endpoint': url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname),
            'operates_on': [],
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': [
                'EPSG:3857'
            ],
            'revision_date': None,
            'title': "Administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje",
        }
    check_metadata(client, workspace, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('ensure_layman')
@pytest.mark.timeout(60)
def test_post_maps_complex(client):
    with app.app_context():
        workspace = 'testuser1'
        mapname = 'libe'
        title = 'Liberecký kraj: Administrativní členění'
        description = 'Libovolný popis'
        rest_path = url_for('rest_workspace_maps.post', workspace=workspace)
        file_paths = [
            'sample/layman.map/full.json',
        ]
        for file_path in file_paths:
            assert os.path.isfile(file_path)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.post(rest_path, data={
                'file': files,
                'name': mapname,
                'title': title,
                'description': description,
            })
        assert response.status_code == 200
        resp_json = response.get_json()
        # print('resp_json', resp_json)
        assert len(resp_json) == 1
        assert resp_json[0]['name'] == mapname
        uuid_str = resp_json[0]['uuid']

        publication_counter.increase()
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': publication_counter.get()
        })

    with app.app_context():
        response = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname))
        assert response.status_code == 200
        resp_json = response.get_json()
        assert resp_json['name'] == mapname
        assert resp_json['uuid'] == uuid_str
        assert resp_json['url'] == url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname)
        assert resp_json['title'] == title
        assert resp_json['description'] == description
        map_file = resp_json['file']
        assert 'status' not in map_file
        assert 'path' in map_file
        assert map_file['url'] == url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname)
        thumbnail = resp_json['thumbnail']
        assert 'status' in thumbnail
        assert thumbnail['status'] in ['PENDING', 'STARTED']

    with app.app_context():
        # assert another PATCH is not possible now
        response = client.patch(url_for('rest_workspace_map.patch', workspace=workspace, mapname=mapname), data={
            'title': 'abcd',
        })
        assert response.status_code == 400
        resp_json = response.get_json()
        assert resp_json['code'] == 49

    # continue with thumbnail assertion
    with app.app_context():
        map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace,
                                          mapname=mapname)).get_json()

    with app.app_context():
        response = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname))
        assert response.status_code == 200
        resp_json = response.get_json()
        thumbnail = resp_json['thumbnail']
        assert 'status' not in thumbnail
        assert 'path' in thumbnail
        assert thumbnail['url'] == url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname)

    with app.app_context():
        response = client.get(url_for('rest_workspace_map_file.get', workspace=workspace, mapname=mapname))
        assert response.status_code == 200
        resp_json = response.get_json()
        assert resp_json['name'] == mapname
        assert resp_json['title'] == title
        assert resp_json['abstract'] == description
        user_json = resp_json['user']
        assert user_json['name'] == workspace
        assert user_json['email'] == ''
        assert len(user_json) == 2
        assert 'groups' not in resp_json

    # continue with metadata assertion
    with app.app_context():
        map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)).get_json()
    while 'status' in map_info['metadata'] and map_info['metadata']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace,
                                          mapname=mapname)).get_json()

    with app.app_context():
        expected_md_values = {
            'abstract': "Libovoln\u00fd popis",
            'extent': [
                14.62,
                50.58,
                15.42,
                50.82
            ],
            'graphic_url': url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname),
            'identifier': {
                "identifier": url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
                "label": "libe"
            },
            'map_endpoint': url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
            'map_file_endpoint': url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname),
            'operates_on': [],
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': [
                'EPSG:3857'
            ],
            'revision_date': None,
            'title': "Libereck\u00fd kraj: Administrativn\u00ed \u010dlen\u011bn\u00ed",
        }
    check_metadata(client, workspace, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('ensure_layman')
def test_patch_map(client):
    with app.app_context():
        workspace = 'testuser1'
        mapname = 'administrativni_cleneni_libereckeho_kraje'
        uuid_str = map_uuid.get_map_uuid(workspace, mapname)
        rest_path = url_for('rest_workspace_map.patch', workspace=workspace, mapname=mapname)

        file_paths = [
            'sample/layman.map/full2.json',
        ]
        for file in file_paths:
            assert os.path.isfile(file)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.patch(rest_path, data={
                'file': files,
            })
        assert response.status_code == 200
        resp_json = response.get_json()
        # print('resp_json', resp_json)

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': publication_counter.get()
        })

        assert resp_json['uuid'] == uuid_str
        assert resp_json['url'] == url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname)
        get_json = client.get(rest_path).get_json()
        assert get_json['title'] == "Jiné administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
        assert get_json['description'] == "Jiný popis"
        map_file = get_json['file']
        assert 'status' not in map_file
        assert 'path' in map_file
        assert map_file['url'] == url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname)
        thumbnail = get_json['thumbnail']
        assert 'status' in thumbnail
        assert thumbnail['status'] in ['PENDING', 'STARTED']

    with app.app_context():
        map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace,
                                          mapname=mapname)).get_json()

    with app.app_context():
        response = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname))
        assert response.status_code == 200
        resp_json = response.get_json()
        thumbnail = resp_json['thumbnail']
        assert 'status' not in thumbnail
        assert 'path' in thumbnail
        assert thumbnail['url'] == url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname)

    with app.app_context():
        response = client.get(url_for('rest_workspace_map_file.get', workspace=workspace, mapname=mapname))
        assert response.status_code == 200
        resp_json = response.get_json()
        assert resp_json['name'] == mapname
        assert resp_json['title'] == "Jiné administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
        assert resp_json['abstract'] == "Jiný popis"
        user_json = resp_json['user']
        assert user_json['name'] == workspace
        assert user_json['email'] == ''
        assert len(user_json) == 2
        assert 'groups' not in resp_json

    with app.app_context():
        map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)).get_json()
    while 'status' in map_info['metadata'] and map_info['metadata']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace,
                                          mapname=mapname)).get_json()

    with app.app_context():
        title = 'Nový název'
        response = client.patch(rest_path, data={
            'title': title,
        })
        assert response.status_code == 200, response.get_json()
        get_json = client.get(rest_path).get_json()
        assert get_json['title'] == "Nový název"
        assert get_json['description'] == "Jiný popis"

    with app.app_context():
        description = 'Nový popis'
        response = client.patch(rest_path, data={
            'description': description,
        })
        assert response.status_code == 200
        get_json = client.get(rest_path).get_json()
        assert get_json['title'] == "Nový název"
        assert get_json['description'] == "Nový popis"

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': publication_counter.get()
        })

    with app.app_context():
        expected_md_values = {
            'abstract': "Nov\u00fd popis",
            'extent': [
                14.623,
                50.58,
                15.42,
                50.82
            ],
            'graphic_url': url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname),
            'identifier': {
                "identifier": url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
                "label": "administrativni_cleneni_libereckeho_kraje"
            },
            'map_endpoint': url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
            'map_file_endpoint': url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname),
            'operates_on': [],
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': [
                'EPSG:3857'
            ],
            'revision_date': TODAY_DATE,
            'title': "Nov\u00fd n\u00e1zev",
        }
    check_metadata(client, workspace, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('ensure_layman')
def test_delete_map(client):
    with app.app_context():
        workspace = 'testuser1'
        mapname = 'administrativni_cleneni_libereckeho_kraje'
        rest_path = url_for('rest_workspace_map.delete_map', workspace=workspace, mapname=mapname)
        response = client.delete(rest_path)
        assert response.status_code == 200
        resp_json = response.get_json()
        uuid_str = resp_json['uuid']
        md_record_url = f"http://micka:80/record/basic/m-{uuid_str}"
        response = requests.get(md_record_url, auth=settings.CSW_BASIC_AUTHN,
                                timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        response.raise_for_status()
        assert 'Záznam nenalezen' in response.text
        assert mapname not in response.text

        publication_counter.decrease()
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': publication_counter.get()
        })

    with app.app_context():
        rest_path = url_for('rest_workspace_map.delete_map', workspace=workspace, mapname=mapname)
        response = client.delete(rest_path)
        assert response.status_code == 404
        resp_json = response.get_json()
        assert resp_json['code'] == 26

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': publication_counter.get()
        })


@pytest.mark.usefixtures('ensure_layman')
def test_map_composed_from_local_layers(client):
    with app.app_context():
        workspace = 'testuser1'
        rest_path = url_for('rest_workspace_layers.post', workspace=workspace)

        layername1 = 'mista'
        relative_file_paths = [
            'tmp/naturalearth/110m/cultural/ne_110m_populated_places.cpg',
            'tmp/naturalearth/110m/cultural/ne_110m_populated_places.dbf',
            'tmp/naturalearth/110m/cultural/ne_110m_populated_places.prj',
            'tmp/naturalearth/110m/cultural/ne_110m_populated_places.shp',
            'tmp/naturalearth/110m/cultural/ne_110m_populated_places.shx',
        ]
        file_paths = [os.path.join(os.getcwd(), fp) for fp in relative_file_paths]
        for file in file_paths:
            assert os.path.isfile(file)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.post(rest_path, data={
                'file': files,
                'name': layername1,
            })
        assert response.status_code == 200
        layer1uuid = response.get_json()[0]['uuid']

    # If no sleep, Micka throws 500
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
        for file in file_paths:
            assert os.path.isfile(file)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.post(rest_path, data={
                'file': files,
                'name': layername2,
            })
        assert response.status_code == 200
        layer2uuid = response.get_json()[0]['uuid']

    with app.app_context():
        keys_to_check = ['db', 'wms', 'wfs', 'thumbnail', 'metadata']
        layer_info = client.get(url_for('rest_workspace_layer.get', workspace=workspace, layername=layername1)).get_json()
        max_attempts = 100
        num_attempts = 1
    while num_attempts < max_attempts and any(('status' in layer_info[key] for key in keys_to_check)):
        time.sleep(0.1)
        # print('layer_info1', layer_info)
        with app.app_context():
            layer_info = client.get(url_for('rest_workspace_layer.get', workspace=workspace, layername=layername1)).get_json()
        num_attempts += 1
    assert num_attempts < max_attempts, f"Max attempts reached, layer1info={layer_info}"
    wms_url1 = layer_info['wms']['url']

    with app.app_context():
        layer_info = client.get(url_for('rest_workspace_layer.get', workspace=workspace, layername=layername2)).get_json()
        num_attempts = 1
    while any(('status' in layer_info[key] for key in keys_to_check)):
        time.sleep(0.1)
        # print('layer_info2', layer_info)
        with app.app_context():
            layer_info = client.get(url_for('rest_workspace_layer.get', workspace=workspace, layername=layername2)).get_json()
        num_attempts += 1
    assert num_attempts < max_attempts, f"Max attempts reached, layer2info={layer_info}"
    wms_url2 = layer_info['wms']['url']

    expected_url = 'http://localhost:8000/geoserver/testuser1_wms/ows'
    assert wms_url1 == expected_url
    assert wms_url2 == expected_url

    with app.app_context():
        mapname = 'svet'
        rest_path = url_for('rest_workspace_maps.post', workspace=workspace)
        file_paths = [
            'sample/layman.map/internal_url.json',
        ]
        for file in file_paths:
            assert os.path.isfile(file)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.post(rest_path, data={
                'file': files,
                'name': mapname,
            })
        assert response.status_code == 200
        resp_json = response.get_json()
        # print('resp_json', resp_json)
        assert len(resp_json) == 1
        assert resp_json[0]['name'] == mapname

    with app.app_context():
        map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)).get_json()
        thumbnail = map_info['thumbnail']
        assert 'status' in thumbnail
        assert thumbnail['status'] in ['PENDING', 'STARTED']

    with app.app_context():
        map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)).get_json()
    while 'status' in map_info['thumbnail'] and map_info['thumbnail']['status'] in ['PENDING', 'STARTED', 'SUCCESS']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace,
                                          mapname=mapname)).get_json()

    with app.app_context():
        response = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname))
        assert response.status_code == 200
        resp_json = response.get_json()
        thumbnail = resp_json['thumbnail']
        assert 'status' not in thumbnail
        assert 'path' in thumbnail
        assert thumbnail['url'] == url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname)

        # uuid.check_redis_consistency(expected_publ_num_by_type={
        #     f'{MAP_TYPE}': num_maps_before_test + 2
        # })

    with app.app_context():
        map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)).get_json()
    while 'status' in map_info['metadata'] and map_info['metadata']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        with app.app_context():
            map_info = client.get(url_for('rest_workspace_map.get', workspace=workspace,
                                          mapname=mapname)).get_json()

    with app.app_context():
        # assert metadata file is the same as filled template except for UUID and dates
        template_path, prop_values = csw.get_template_path_and_values(workspace, mapname, http_method='post',
                                                                      actor_name=settings.ANONYM_USER)
        xml_file_object = micka_common_util.fill_xml_template_as_pretty_file_object(template_path, prop_values,
                                                                                    csw.METADATA_PROPERTIES)
        expected_path = 'src/layman/map/rest_test_filled_template.xml'
        with open(expected_path, encoding="utf-8") as file:
            expected_lines = file.readlines()
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

    with app.app_context():
        expected_md_values = {
            'abstract': "World places and boundaries abstract",
            'extent': [
                -35.0,
                -48.5,
                179.0,
                81.5
            ],
            'graphic_url': url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname),
            'identifier': {
                "identifier": url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
                "label": "svet"
            },
            'map_endpoint': url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
            'map_file_endpoint': url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname),
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
                'EPSG:3857'
            ],
            'revision_date': None,
            'title': "World places and boundaries",
        }
    check_metadata(client, workspace, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('ensure_layman')
def test_just_delete_publications(client):
    flask_client.delete_map('testuser1', 'libe', client)
    flask_client.delete_map('testuser1', 'svet', client)
    flask_client.delete_layer('testuser1', 'hranice', client)
    flask_client.delete_layer('testuser1', 'mista', client)
