import io
import os
from multiprocessing import Process
import requests
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import filecmp
import difflib

import pytest
from flask import url_for

import sys
del sys.modules['layman']

from . import util, LAYER_TYPE
from .geoserver.util import get_feature_type, wms_proxy
from layman import app as app
from layman import settings
from layman.layer.filesystem import uuid as layer_uuid
from layman import uuid
from layman.layer import db
from layman import celery as celery_util
from .micka import csw
from layman.common.micka import util as micka_common_util


min_geojson = """
{
  "type": "Feature",
  "geometry": null,
  "properties": null
}
"""

num_layers_before_test = 0


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
        global num_layers_before_test
        num_layers_before_test = len(publs_by_type[LAYER_TYPE])
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
def test_wrong_value_of_user(client):
    usernames = [' ', '2a', 'ě', ';', '?', 'ABC']
    for username in usernames:
        rv = client.post(url_for('rest_layers.post', username=username))
        resp_json = rv.get_json()
        # print('username', username)
        # print(resp_json)
        assert rv.status_code==400
        assert resp_json['code']==2
        assert resp_json['detail']['parameter']=='user'


@pytest.mark.usefixtures('app_context')
def test_wrong_value_of_layername(client):
    username = 'testuser1'
    layernames = [' ', '2a', 'ě', ';', '?', 'ABC']
    for layername in layernames:
        rv = client.get(url_for('rest_layer.get', username=username, layername=layername))
        resp_json = rv.get_json()
        # print('username', username)
        # print(resp_json)
        assert rv.status_code==400
        assert resp_json['code']==2
        assert resp_json['detail']['parameter']=='layername'


@pytest.mark.usefixtures('app_context')
def test_no_file(client):
    rv = client.post(url_for('rest_layers.post', username='testuser1'))
    assert rv.status_code==400
    resp_json = rv.get_json()
    # print('resp_json', resp_json)
    assert resp_json['code']==1
    assert resp_json['detail']['parameter']=='file'


@pytest.mark.usefixtures('app_context')
def test_username_schema_conflict(client):
    if len(settings.PG_NON_USER_SCHEMAS) == 0:
        pass
    rv = client.post(url_for('rest_layers.post', username=settings.PG_NON_USER_SCHEMAS[0]))
    assert rv.status_code==409
    resp_json = rv.get_json()
    # print(resp_json)
    assert resp_json['code'] == 35
    assert resp_json['detail']['reserved_by'] == db.__name__
    assert 'reason' not in resp_json['detail']
    for schema_name in [
        'pg_catalog',
        'pg_toast',
        'information_schema',
    ]:
        rv = client.post(url_for('rest_layers.post', username=schema_name), data={
            'file': [
                (io.BytesIO(min_geojson.encode()), '/file.geojson')
            ]
        })
        resp_json = rv.get_json()
        # print(resp_json)
        assert rv.status_code == 409
        assert resp_json['code'] == 35
        assert resp_json['detail']['reserved_by'] == db.__name__
        assert resp_json['detail']['reason'] == 'DB schema owned by another than layman user'


@pytest.mark.usefixtures('app_context')
def test_layername_db_object_conflict(client):
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
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


@pytest.mark.usefixtures('app_context')
def test_get_layers_testuser1_v1(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username))
    assert rv.status_code==200
    # resp_json = rv.get_json()
    # assert len(resp_json) == 0
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 0
    })


def wait_till_ready(username, layername):
    last_task = util._get_layer_task(username, layername)
    while last_task is not None and not celery_util.is_task_ready(last_task):
        time.sleep(0.1)
        last_task = util._get_layer_task(username, layername)


@pytest.mark.usefixtures('app_context')
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
        rv = client.post(rest_path, data={
            'file': files
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    layername = 'ne_110m_admin_0_countries'

    last_task = util._get_layer_task(username, layername)
    assert last_task is not None and not celery_util.is_task_ready(last_task)
    layer_info = util.get_layer_info(username, layername)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'metadata']
    for key_to_check in keys_to_check:
            assert 'status' in layer_info[key_to_check]

    # TODO for some reason this hangs forever on get() if run (either with src/layman/authz/read_everyone_write_owner_auth2_test.py::test_authn_map_access_rights or src/layman/authn/oauth2_test.py::test_patch_current_user_without_username) and with src/layman/common/metadata/util.csw_insert
    # last_task['last'].get()
    # e.g. python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/authn/oauth2_test.py::test_patch_current_user_without_username src/layman/layer/rest_test.py::test_post_layers_simple
    # this can badly affect also .get(propagate=False) in layman.celery.abort_task_chain
    # but hopefully this is only related to magic flask&celery test suite
    wait_till_ready(username, layername)

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

    layer_info = client.get(url_for('rest_layer.get', username=username, layername=layername)).get_json()
    assert set(layer_info['metadata'].keys()) == {'identifier', 'csw_url', 'record_url'}
    assert layer_info['metadata']['identifier'] == f"m-{uuid_str}"
    assert layer_info['metadata']['csw_url'] == settings.CSW_PROXY_URL
    md_record_url = f"http://micka:80/record/basic/m-{uuid_str}"
    assert layer_info['metadata']['record_url'].replace("http://localhost:3080", "http://micka:80") == md_record_url
    r = requests.get(md_record_url, auth=settings.CSW_BASIC_AUTHN)
    r.raise_for_status()
    assert layername in r.text

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 1
    })


@pytest.mark.usefixtures('app_context')
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
        rv = client.post(rest_path, data={
            'file': files,
            'name': layername,
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    last_task = util._get_layer_task(username, layername)
    assert last_task is not None and not celery_util.is_task_ready(last_task)

    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
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
        f'{LAYER_TYPE}': num_layers_before_test + 2
    })


@pytest.mark.usefixtures('app_context')
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
        f'{LAYER_TYPE}': num_layers_before_test + 2
    })


@pytest.mark.usefixtures('app_context')
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
        rv = client.post(rest_path, data={
            'file': files,
            'name': layername
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    last_task = util._get_layer_task(username, layername)
    assert last_task is not None and not celery_util.is_task_ready(last_task)
    wait_till_ready(username, layername)
    # last_task['last'].get()

    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert 'ne_110m_admin_0_countries_shp' in wms.contents
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 3
    })

    # assert metadata file is the same as filled template except for UUID
    template_path, template_values = csw.get_template_path_and_values(username, layername)
    xml_file_object = micka_common_util.fill_template_as_pretty_file_object(template_path, template_values)
    expected_path = 'src/layman/layer/rest_test_filled_template.xml'
    with open(expected_path) as f:
        expected_lines = f.readlines()
    diff_lines = list(difflib.unified_diff([l.decode('utf-8') for l in xml_file_object.readlines()], expected_lines))
    assert len(diff_lines) == 29, ''.join(diff_lines)
    plus_lines = [l for l in diff_lines if l.startswith('+ ')]
    assert len(plus_lines) == 3
    minus_lines = [l for l in diff_lines if l.startswith('- ')]
    assert len(minus_lines) == 3
    plus_line = plus_lines[0]
    assert plus_line == '+    <gco:CharacterString>m-81c0debe-b2ea-4829-9b16-581083b29907</gco:CharacterString>\n'
    minus_line = minus_lines[0]
    assert minus_line.startswith('-    <gco:CharacterString>m') and minus_line.endswith('</gco:CharacterString>\n')
    plus_line = plus_lines[1]
    assert plus_line == '+    <gco:Date>2007-05-25</gco:Date>\n'
    minus_line = minus_lines[1]
    assert minus_line.startswith('-    <gco:Date>') and minus_line.endswith('</gco:Date>\n')
    plus_line = plus_lines[2]
    assert plus_line == '+                <gco:Date>2019-12-07</gco:Date>\n'
    minus_line = minus_lines[2]
    assert minus_line.startswith('-                <gco:Date>') and minus_line.endswith('</gco:Date>\n')


@pytest.mark.usefixtures('app_context')
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
        f'{LAYER_TYPE}': num_layers_before_test + 3
    })


@pytest.mark.usefixtures('app_context')
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

    last_task = util._get_layer_task(username, layername)
    assert last_task is not None and not celery_util.is_task_ready(last_task)
    wait_till_ready(username, layername)
    # last_task['last'].get()
    assert celery_util.is_task_ready(last_task)

    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert 'countries' in wms.contents
    assert wms['countries'].title == 'staty'
    assert wms['countries'].abstract == 'popis států'
    assert wms['countries'].styles[
        username+':countries']['title'] == 'Generic Blue'

    assert layername != ''
    rest_path = url_for('rest_layer.get', username=username, layername=layername)
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
        'metadata',
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
        f'{LAYER_TYPE}': num_layers_before_test + 4
    })


@pytest.mark.usefixtures('app_context')
def test_get_layers_testuser1_v2(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username))
    assert rv.status_code==200
    resp_json = rv.get_json()
    # assert len(resp_json) == 3
    layernames = [l['name'] for l in resp_json]
    for ln in [
        'countries_concurrent',
        'ne_110m_admin_0_countries',
        'ne_110m_admin_0_countries_shp'
    ]:
        assert ln in layernames

    username = 'testuser2'
    rv = client.get(url_for('rest_layers.get', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 1
    assert resp_json[0]['name'] == 'countries'

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 4
    })


@pytest.mark.usefixtures('app_context')
def test_patch_layer_title(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries'
    rest_path = url_for('rest_layer.patch', username=username, layername=layername)
    rv = client.patch(rest_path, data={
        'title': "New Title of Countries",
        'description': "and new description"
    })
    assert rv.status_code == 200, rv.get_json()

    last_task = util._get_layer_task(username, layername)
    assert last_task is not None and celery_util.is_task_ready(last_task)

    resp_json = rv.get_json()
    assert resp_json['title'] == "New Title of Countries"
    assert resp_json['description'] == "and new description"
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 4
    })


@pytest.mark.usefixtures('app_context')
def test_patch_layer_style(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries'
    rest_path = url_for('rest_layer.patch', username=username, layername=layername)
    sld_path = 'sample/style/generic-blue.xml'
    assert os.path.isfile(sld_path)
    rv = client.patch(rest_path, data={
        'sld': (open(sld_path, 'rb'), os.path.basename(sld_path)),
        'title': 'countries in blue'
    })
    assert rv.status_code == 200

    last_task = util._get_layer_task(username, layername)
    # TODO
    # Time to generate testing thumbnail is probably shorter than getting & parsing WMS/WFS capabilities documents
    # so it's finished before PATCH request is completed
    #
    # assert last_task is not None and not util._is_task_ready(last_task)
    # resp_json = rv.get_json()
    # keys_to_check = ['thumbnail']
    # for key_to_check in keys_to_check:
    #         assert 'status' in resp_json[key_to_check]
    wait_till_ready(username, layername)
    # last_task['last'].get()

    resp_json = rv.get_json()
    assert resp_json['title'] == "countries in blue"

    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert layername in wms.contents
    assert wms[layername].title == 'countries in blue'
    assert wms[layername].styles[
        username+':'+layername]['title'] == 'Generic Blue'
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 4
    })


@pytest.mark.usefixtures('app_context')
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
        f'{LAYER_TYPE}': num_layers_before_test + 5
    })

    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    rv = client.delete(rest_path)
    assert rv.status_code == 200
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 4
    })


def test_patch_layer_data(client):
    with app.app_context():
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
            rv = client.patch(rest_path, data={
                'file': files,
                'title': 'populated places'
            })
            assert rv.status_code == 200
        finally:
            for fp in files:
                fp[0].close()

        last_task = util._get_layer_task(username, layername)
        assert last_task is not None and not celery_util.is_task_ready(last_task)
        resp_json = rv.get_json()
        keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'metadata']
        for key_to_check in keys_to_check:
                assert 'status' in resp_json[key_to_check]
        wait_till_ready(username, layername)
        # last_task['last'].get()

    with app.app_context():
        rest_path = url_for('rest_layer.get', username=username, layername=layername)
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
            f'{LAYER_TYPE}': num_layers_before_test + 4
        })


@pytest.mark.usefixtures('app_context')
def test_patch_layer_concurrent_and_delete_it(client):
    with app.app_context():
        username = 'testuser2'
        layername = 'countries'
        rest_path = url_for('rest_layer.patch', username=username, layername=layername)
        file_paths = [
            'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
        ]
        for fp in file_paths:
            assert os.path.isfile(fp)

        uuid_str = layer_uuid.get_layer_uuid(username, layername)
        assert uuid.is_valid_uuid(uuid_str)

        files = []
        try:
            files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in
                     file_paths]
            rv = client.patch(rest_path, data={
                'file': files,
                'title': 'populated places'
            })
            assert rv.status_code == 200
        finally:
            for fp in files:
                fp[0].close()
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': num_layers_before_test + 4
        })

        last_task = util._get_layer_task(username, layername)
        assert last_task is not None and not celery_util.is_task_ready(last_task)

    with app.app_context():
        try:
            files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in
                     file_paths]
            rv = client.patch(rest_path, data={
                'file': files,
            })
            assert rv.status_code == 400, rv.get_json()
            resp_json = rv.get_json()
            assert resp_json['code'] == 19
        finally:
            for fp in files:
                fp[0].close()
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': num_layers_before_test + 4
        })

    with app.app_context():
        rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
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
            f'{LAYER_TYPE}': num_layers_before_test + 3
        })


@pytest.mark.usefixtures('app_context')
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
        rv = client.post(rest_path, data={
            'file': files
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    layername = 'ne_10m_admin_0_countries'

    time.sleep(1)

    last_task = util._get_layer_task(username, layername)
    assert last_task is not None and not celery_util.is_task_ready(last_task)
    layer_info = util.get_layer_info(username, layername)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'metadata']
    for key_to_check in keys_to_check:
            assert 'status' in layer_info[key_to_check]

    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    rv = client.delete(rest_path)
    assert rv.status_code == 200
    rv = client.get(url_for('rest_layer.get', username=username, layername=layername))
    resp_json = rv.get_json()
    # print(resp_json)
    assert rv.status_code == 404
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 3
    })


@pytest.mark.usefixtures('app_context')
def test_delete_layer(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries'
    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    rv = client.delete(rest_path)
    assert rv.status_code == 200
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 2
    })

    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    rv = client.delete(rest_path)
    assert rv.status_code == 404
    resp_json = rv.get_json()
    assert resp_json['code'] == 15


@pytest.mark.usefixtures('app_context')
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
        rv = client.post(rest_path, data={
            'file': files
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    layername = 'zero_length_attribute'

    layer_info = util.get_layer_info(username, layername)
    while 'status' in layer_info['db_table'] and layer_info['db_table']['status'] in ['PENDING', 'STARTED']:
        time.sleep(0.1)
        layer_info = util.get_layer_info(username, layername)
    assert layer_info['db_table']['status'] == 'FAILURE'
    assert layer_info['db_table']['error']['code'] == 28

    rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
    rv = client.delete(rest_path)
    assert rv.status_code == 200
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 2
    })


@pytest.mark.usefixtures('app_context')
def test_get_layers_testuser2(client):
    username = 'testuser2'
    rv = client.get(url_for('rest_layers.get', username=username))
    assert rv.status_code==200
    resp_json = rv.get_json()
    assert len(resp_json) == 0
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 2
    })


