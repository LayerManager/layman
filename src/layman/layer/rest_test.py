import io
import os
import requests
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import pytest
from flask import url_for

from . import util, LAYER_TYPE
from .geoserver.util import get_feature_type, wms_proxy
from layman import app as layman
from layman import settings
from layman.layer.filesystem import uuid as layer_uuid
from layman import uuid, util as layman_util

min_geojson = """
{
  "type": "Feature",
  "geometry": null,
  "properties": null
}
"""

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

def test_wrong_value_of_user(client):
    usernames = [' ', '2a', 'ě', ';', '?', 'ABC']
    for username in usernames:
        with layman.app_context():
            rv = client.post(url_for('rest_layers.post', username=username))
        resp_json = rv.get_json()
        # print('username', username)
        # print(resp_json)
        assert rv.status_code==400
        assert resp_json['code']==2
        assert resp_json['detail']['parameter']=='user'


def test_no_file(client):
    with layman.app_context():
        rv = client.post(url_for('rest_layers.post', username='testuser1'))
    assert rv.status_code==400
    resp_json = rv.get_json()
    # print('resp_json', resp_json)
    assert resp_json['code']==1
    assert resp_json['detail']['parameter']=='file'


def test_username_schema_conflict(client):
    if len(settings.PG_NON_USER_SCHEMAS) == 0:
        pass
    with layman.app_context():
        rv = client.post(url_for('rest_layers.post', username=settings.PG_NON_USER_SCHEMAS[0]))
    assert rv.status_code==409
    resp_json = rv.get_json()
    # print(resp_json)
    assert resp_json['code']==8
    for schema_name in [
        'pg_catalog',
        'pg_toast',
        'information_schema',
    ]:
        with layman.app_context():
            rv = client.post(url_for('rest_layers.post', username=schema_name), data={
                'file': [
                    (io.BytesIO(min_geojson.encode()), '/file.geojson')
                ]
            })
        resp_json = rv.get_json()
        # print(resp_json)
        assert rv.status_code==409
        assert resp_json['code']==10


def test_layername_db_object_conflict(client):
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        with layman.app_context():
            rv = client.post(url_for('rest_layers.post', username='testuser1'), data={
                'file': files,
                'name': 'spatial_ref_sys'
            })
        assert rv.status_code == 409
        resp_json = rv.get_json()
        assert resp_json['code']==9
    finally:
        for fp in files:
            fp[0].close()


def test_get_layers_empty(client):
    username = 'testuser1'
    with layman.app_context():
        rv = client.get(url_for('rest_layers.get', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 0
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 0
    })


def test_post_layers_simple(client):
    username = 'testuser1'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
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
    finally:
        for fp in files:
            fp[0].close()

    layername = 'ne_110m_admin_0_countries'

    last_task = util._get_layer_last_task(username, layername)
    assert last_task is not None and not util._is_task_ready(last_task)
    layer_info = util.get_layer_info(username, layername)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail']
    for key_to_check in keys_to_check:
            assert 'status' in layer_info[key_to_check]

    last_task['last'].get()

    layer_info = util.get_layer_info(username, layername)
    for key_to_check in keys_to_check:
            assert isinstance(layer_info[key_to_check], str) \
                   or 'status' not in layer_info[key_to_check]

    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert layername in wms.contents

    from layman.layer import get_layer_type_def
    from layman.common.filesystem import uuid as common_uuid
    uuid_filename = common_uuid.get_publication_uuid_file(
        get_layer_type_def()['type'], username, layername)
    assert os.path.isfile(uuid_filename)
    uuid_str = None
    with open(uuid_filename, "r") as f:
        uuid_str = f.read().strip()
    assert uuid.is_valid_uuid(uuid_str)
    assert settings.LAYMAN_REDIS.sismember(uuid.UUID_SET_KEY, uuid_str)
    assert settings.LAYMAN_REDIS.exists(uuid.get_uuid_metadata_key(uuid_str))
    assert settings.LAYMAN_REDIS.hexists(
        uuid.get_user_type_names_key(username, '.'.join(__name__.split('.')[:-1])),
        layername
    )

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 1
    })


def test_post_layers_concurrent(client):
    username = 'testuser1'
    layername = 'countries_concurrent'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        with layman.app_context():
            rv = client.post(rest_path, data={
                'file': files,
                'name': layername,
            })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    last_task = util._get_layer_last_task(username, layername)
    assert last_task is not None and not util._is_task_ready(last_task)

    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        with layman.app_context():
            rv = client.post(rest_path, data={
                'file': files,
                'name': layername,
            })
        assert rv.status_code == 409
        resp_json = rv.get_json()
        assert resp_json['code'] == 17
    finally:
        for fp in files:
            fp[0].close()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 2
    })


def test_post_layers_shp_missing_extensions(client):
    username = 'testuser1'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.dbf',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.VERSION.txt',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        with layman.app_context():
            rv = client.post(rest_path, data={
                'file': files,
                'name': 'ne_110m_admin_0_countries_shp'
            })
        resp_json = rv.get_json()
        # print(resp_json)
        assert rv.status_code == 400
        assert resp_json['code']==18
        assert sorted(resp_json['detail']['missing_extensions']) == [
            '.prj', '.shx']
    finally:
        for fp in files:
            fp[0].close()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 2
    })


def test_post_layers_shp(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries_shp'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.cpg',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.dbf',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.prj',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.README.html',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shx',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.VERSION.txt',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        with layman.app_context():
            rv = client.post(rest_path, data={
                'file': files,
                'name': layername
            })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    last_task = util._get_layer_last_task(username, layername)
    assert last_task is not None and not util._is_task_ready(last_task)
    last_task['last'].get()

    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert 'ne_110m_admin_0_countries_shp' in wms.contents
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 3
    })


def test_post_layers_layer_exists(client):
    username = 'testuser1'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
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
        assert rv.status_code==409
        resp_json = rv.get_json()
        assert resp_json['code']==17
    finally:
        for fp in files:
            fp[0].close()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 3
    })

def test_post_layers_complex(client):
    username = 'testuser2'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    sld_path = 'sample/style/generic-blue.xml'
    assert os.path.isfile(sld_path)
    layername = ''
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        with layman.app_context():
            rv = client.post(rest_path, data={
                'file': files,
                'name': 'countries',
                'title': 'staty',
                'description': 'popis států',
                'sld': (open(sld_path, 'rb'), os.path.basename(sld_path)),
            })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        # print(resp_json)
        layername = resp_json[0]['name']
    finally:
        for fp in files:
            fp[0].close()

    last_task = util._get_layer_last_task(username, layername)
    assert last_task is not None and not util._is_task_ready(last_task)
    last_task['last'].get()

    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert 'countries' in wms.contents
    assert wms['countries'].title == 'staty'
    assert wms['countries'].abstract == 'popis států'
    assert wms['countries'].styles[
        username+':countries']['title'] == 'Generic Blue'

    assert layername != ''
    rest_path = url_for('rest_layer.get', username=username, layername=layername)
    with layman.app_context():
        rv = client.get(rest_path)
    assert 200 <= rv.status_code < 300
    resp_json = rv.get_json()
    # print(resp_json)
    assert resp_json['title']=='staty'
    assert resp_json['description']=='popis států'
    for source in [
        'wms',
        'wfs',
        'thumbnail',
        'file',
        'db_table',
    ]:
        assert 'status' not in resp_json[source]

    style_url = urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                    username + '/styles/' + layername)
    r = requests.get(style_url + '.sld',
        auth=settings.LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    sld_file = io.BytesIO(r.content)
    tree = ET.parse(sld_file)
    root = tree.getroot()
    assert root.attrib['version'] == '1.0.0'

    feature_type = get_feature_type(username, 'postgresql', layername)
    attributes = feature_type['attributes']['attribute']
    assert next((
        a for a in attributes if a['name'] == 'sovereignt'
    ), None) is not None
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 4
    })


def test_get_layers(client):
    username = 'testuser1'
    with layman.app_context():
        rv = client.get(url_for('rest_layers.get', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 3
    assert sorted(map(lambda l: l['name'], resp_json)) == [
        'countries_concurrent',
        'ne_110m_admin_0_countries',
        'ne_110m_admin_0_countries_shp'
    ]

    username = 'testuser2'
    with layman.app_context():
        rv = client.get(url_for('rest_layers.get', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 1
    assert resp_json[0]['name'] == 'countries'

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 4
    })


def test_patch_layer_title(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries'
    rest_path = url_for('rest_layer.patch', username=username, layername=layername)
    with layman.app_context():
        rv = client.patch(rest_path, data={
            'title': "New Title of Countries",
            'description': "and new description"
        })
    assert rv.status_code == 200

    last_task = util._get_layer_last_task(username, layername)
    assert last_task is not None and util._is_task_ready(last_task)

    resp_json = rv.get_json()
    assert resp_json['title'] == "New Title of Countries"
    assert resp_json['description'] == "and new description"
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 4
    })


def test_patch_layer_style(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries'
    rest_path = url_for('rest_layer.patch', username=username, layername=layername)
    sld_path = 'sample/style/generic-blue.xml'
    assert os.path.isfile(sld_path)
    with layman.app_context():
        rv = client.patch(rest_path, data={
            'sld': (open(sld_path, 'rb'), os.path.basename(sld_path)),
            'title': 'countries in blue'
        })
    assert rv.status_code == 200

    last_task = util._get_layer_last_task(username, layername)
    assert last_task is not None and not util._is_task_ready(last_task)
    resp_json = rv.get_json()
    keys_to_check = ['thumbnail']
    for key_to_check in keys_to_check:
            assert 'status' in resp_json[key_to_check]
    last_task['last'].get()

    resp_json = rv.get_json()
    assert resp_json['title'] == "countries in blue"

    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert layername in wms.contents
    assert wms[layername].title == 'countries in blue'
    assert wms[layername].styles[
        username+':'+layername]['title'] == 'Generic Blue'
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 4
    })


def test_post_layers_sld_1_1_0(client):
    username = 'testuser1'
    layername = 'countries_sld_1_1_0'
    rest_path = url_for('rest_layers.post', username=username, layername=layername)

    file_paths = [
        'sample/data/test_layer4.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    sld_path = 'sample/style/sld_1_1_0.xml'
    assert os.path.isfile(sld_path)
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        with layman.app_context():
            rv = client.post(rest_path, data={
                'file': files,
                'name': layername,
                'sld': (open(sld_path, 'rb'), os.path.basename(sld_path)),
            })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        # print(resp_json)
        assert layername == resp_json[0]['name']
    finally:
        for fp in files:
            fp[0].close()

    time.sleep(0.5)

    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert layername in wms.contents
    assert wms[layername].title == 'countries_sld_1_1_0'

    style_url = urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                    username + '/styles/' + layername)
    r = requests.get(style_url + '.sld',
        auth=settings.LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    sld_file = io.BytesIO(r.content)
    tree = ET.parse(sld_file)
    root = tree.getroot()
    # for some reason, GeoServer REST API in 2.13.0 transforms SLD 1.1.0 to 1.0.0
    # web interface is not doing this
    # assert root.attrib['version'] == '1.1.0'
    assert root.attrib['version'] == '1.0.0'
    assert root[0][1][1][1][1][0][0].text == '#e31a1c'
    # assert wms[layername].styles[
    #     username+':'+layername]['title'] == 'test_layer2'

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 5
    })

    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    with layman.app_context():
        rv = client.delete(rest_path)
        assert rv.status_code == 200
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': 4
        })


def test_patch_layer_data(client):
    username = 'testuser2'
    layername = 'countries'
    rest_path = url_for('rest_layer.patch', username=username, layername=layername)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in
                 file_paths]
        with layman.app_context():
            rv = client.patch(rest_path, data={
                'file': files,
                'title': 'populated places'
            })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    last_task = util._get_layer_last_task(username, layername)
    assert last_task is not None and not util._is_task_ready(last_task)
    resp_json = rv.get_json()
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail']
    for key_to_check in keys_to_check:
            assert 'status' in resp_json[key_to_check]
    last_task['last'].get()

    rest_path = url_for('rest_layer.get', username=username, layername=layername)
    with layman.app_context():
        rv = client.get(rest_path)
    assert 200 <= rv.status_code < 300

    resp_json = rv.get_json()
    assert resp_json['title'] == "populated places"
    feature_type = get_feature_type(username, 'postgresql', layername)
    attributes = feature_type['attributes']['attribute']
    assert next((
        a for a in attributes if a['name'] == 'sovereignt'
    ), None) is None
    assert next((
        a for a in attributes if a['name'] == 'adm0cap'
    ), None) is not None
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 4
    })


def test_patch_layer_concurrent_and_delete_it(client):
    username = 'testuser2'
    layername = 'countries'
    rest_path = url_for('rest_layer.patch', username=username, layername=layername)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)

    uuid_str = layer_uuid.get_layer_uuid(username, layername)
    assert uuid.is_valid_uuid(uuid_str)

    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in
                 file_paths]
        with layman.app_context():
            rv = client.patch(rest_path, data={
                'file': files,
                'title': 'populated places'
            })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 4
    })

    last_task = util._get_layer_last_task(username, layername)
    assert last_task is not None and not util._is_task_ready(last_task)

    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in
                 file_paths]
        with layman.app_context():
            rv = client.patch(rest_path, data={
                'file': files,
            })
        assert rv.status_code == 400
        resp_json = rv.get_json()
        assert resp_json['code'] == 19
    finally:
        for fp in files:
            fp[0].close()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 4
    })

    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    with layman.app_context():
        rv = client.delete(rest_path)
    assert rv.status_code == 200

    from layman.layer import get_layer_type_def
    from layman.common.filesystem import uuid as common_uuid
    uuid_filename = common_uuid.get_publication_uuid_file(
        get_layer_type_def()['type'], username, layername)
    assert not os.path.isfile(uuid_filename)
    assert not settings.LAYMAN_REDIS.sismember(uuid.UUID_SET_KEY, uuid_str)
    assert not settings.LAYMAN_REDIS.exists(uuid.get_uuid_metadata_key(uuid_str))
    assert not settings.LAYMAN_REDIS.hexists(
        uuid.get_user_type_names_key(username, '.'.join(__name__.split('.')[:-1])),
        layername
    )
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 3
    })


def test_post_layers_long_and_delete_it(client):
    username = 'testuser1'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
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
    finally:
        for fp in files:
            fp[0].close()

    layername = 'ne_10m_admin_0_countries'

    time.sleep(1)

    last_task = util._get_layer_last_task(username, layername)
    assert last_task is not None and not util._is_task_ready(last_task)
    layer_info = util.get_layer_info(username, layername)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail']
    for key_to_check in keys_to_check:
            assert 'status' in layer_info[key_to_check]

    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    with layman.app_context():
        rv = client.delete(rest_path)
    assert rv.status_code == 200
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 3
    })


def test_delete_layer(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries'
    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    with layman.app_context():
        rv = client.delete(rest_path)
    assert rv.status_code == 200
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 2
    })

    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    with layman.app_context():
        rv = client.delete(rest_path)
    assert rv.status_code == 404
    resp_json = rv.get_json()
    assert resp_json['code'] == 15


def test_post_layers_zero_length_attribute(client):
    username = 'testuser1'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'sample/data/zero_length_attribute.geojson',
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
    finally:
        for fp in files:
            fp[0].close()

    layername = 'zero_length_attribute'

    layer_info = util.get_layer_info(username, layername)
    while 'status' in layer_info['db_table'] and layer_info['db_table']['status'] == 'PENDING':
        time.sleep(0.1)
        layer_info = util.get_layer_info(username, layername)
    assert layer_info['db_table']['status'] == 'FAILURE'
    assert layer_info['db_table']['error']['code'] == 28

    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    with layman.app_context():
        rv = client.delete(rest_path)
        assert rv.status_code == 200
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': 2
        })


def test_get_layers_empty_again(client):
    username = 'testuser2'
    with layman.app_context():
        rv = client.get(url_for('rest_layers.get', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 0
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': 2
    })


