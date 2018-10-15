import io

import pytest
import unittest
from flask import url_for

from layman.geoserver.util import get_feature_type, wms_proxy
from layman import app as layman
from layman import util
from .settings import *

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
            rv = client.post(url_for('post_layers', username=username))
        resp_json = rv.get_json()
        # print('username', username)
        # print(resp_json)
        assert rv.status_code==400
        assert resp_json['code']==2
        assert resp_json['detail']['parameter']=='user'


def test_no_file(client):
    with layman.app_context():
        rv = client.post(url_for('post_layers', username='testuser1'))
    assert rv.status_code==400
    resp_json = rv.get_json()
    # print('resp_json', resp_json)
    assert resp_json['code']==1
    assert resp_json['detail']['parameter']=='file'


def test_username_schema_conflict(client):
    if len(PG_NON_USER_SCHEMAS) == 0:
        pass
    with layman.app_context():
        rv = client.post(url_for('post_layers', username=PG_NON_USER_SCHEMAS[0]))
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
            rv = client.post(url_for('post_layers', username=schema_name), data={
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
            rv = client.post(url_for('post_layers', username='testuser1'), data={
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
        rv = client.get(url_for('get_layers', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 0


def test_post_layers_simple(client):
    username = 'testuser1'
    rest_path = url_for('post_layers', username=username)
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

    layer_tasks = util.get_layer_not_ready_tasks(username, layername)
    assert len(layer_tasks) == 1

    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        with layman.app_context():
            rv = client.post(rest_path, data={
                'file': files
            })
        assert rv.status_code == 409
        resp_json = rv.get_json()
        assert resp_json['code'] == 17
    finally:
        for fp in files:
            fp[0].close()

    layer_info = util.get_layer_info(username, layername)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail']
    for key_to_check in keys_to_check:
            assert 'status' in layer_info[key_to_check]

    layer_tasks[0]['last'].get()

    layer_info = util.get_layer_info(username, layername)
    for key_to_check in keys_to_check:
            assert isinstance(layer_info[key_to_check], str) \
                   or 'status' not in layer_info[key_to_check]

    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert layername in wms.contents


def test_post_layers_shp_missing_extensions(client):
    username = 'testuser1'
    rest_path = url_for('post_layers', username=username)
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


def test_post_layers_shp(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries_shp'
    rest_path = url_for('post_layers', username=username)
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

    layer_tasks = util.get_layer_not_ready_tasks(username, layername)
    assert len(layer_tasks) == 1
    layer_tasks[0]['last'].get()

    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert 'ne_110m_admin_0_countries_shp' in wms.contents


def test_post_layers_layer_exists(client):
    username = 'testuser1'
    rest_path = url_for('post_layers', username=username)
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

def test_post_layers_complex(client):
    username = 'testuser2'
    rest_path = url_for('post_layers', username=username)
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

    layer_tasks = util.get_layer_not_ready_tasks(username, layername)
    assert len(layer_tasks) == 1
    layer_tasks[0]['last'].get()

    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert 'countries' in wms.contents
    assert wms['countries'].title == 'staty'
    assert wms['countries'].abstract == 'popis států'
    assert wms['countries'].styles[
        username+':countries']['title'] == 'Generic Blue'

    assert layername != ''
    rest_path = url_for('get_layer', username=username, layername=layername)
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

    feature_type = get_feature_type(username, 'postgresql', layername)
    attributes = feature_type['attributes']['attribute']
    assert next((
        a for a in attributes if a['name'] == 'sovereignt'
    ), None) is not None


def test_get_layers(client):
    username = 'testuser1'
    with layman.app_context():
        rv = client.get(url_for('get_layers', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 2
    assert sorted(map(lambda l: l['name'], resp_json)) == [
        'ne_110m_admin_0_countries',
        'ne_110m_admin_0_countries_shp'
    ]

    username = 'testuser2'
    with layman.app_context():
        rv = client.get(url_for('get_layers', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 1
    assert resp_json[0]['name'] == 'countries'


def test_put_layer_title(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries'
    rest_path = url_for('put_layer', username=username, layername=layername)
    with layman.app_context():
        rv = client.put(rest_path, data={
            'title': "New Title of Countries",
            'description': "and new description"
        })
    assert rv.status_code == 200

    layer_tasks = util.get_layer_not_ready_tasks(username, layername)
    assert len(layer_tasks) == 0

    resp_json = rv.get_json()
    assert resp_json['title'] == "New Title of Countries"
    assert resp_json['description'] == "and new description"

def test_put_layer_style(client):
    username = 'testuser1'
    layername = 'ne_110m_admin_0_countries'
    rest_path = url_for('put_layer', username=username, layername=layername)
    sld_path = 'sample/style/generic-blue.xml'
    assert os.path.isfile(sld_path)
    with layman.app_context():
        rv = client.put(rest_path, data={
            'sld': (open(sld_path, 'rb'), os.path.basename(sld_path)),
            'title': 'countries in blue'
        })
    assert rv.status_code == 200

    resp_json = rv.get_json()
    assert resp_json['title'] == "countries in blue"

    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert layername in wms.contents
    assert wms[layername].title == 'countries in blue'
    assert wms[layername].styles[
        username+':'+layername]['title'] == 'Generic Blue'


def test_put_layer_data(client):
    username = 'testuser2'
    layername = 'countries'
    rest_path = url_for('put_layer', username=username, layername=layername)
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
            rv = client.put(rest_path, data={
                'file': files,
                'title': 'populated places'
            })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

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


def test_delete_layer(client):
    username = 'testuser2'
    layername = 'countries'
    rest_path = url_for('delete_layer', username=username, layername=layername)
    with layman.app_context():
        rv = client.delete(rest_path)
    assert rv.status_code == 200

    rest_path = url_for('delete_layer', username=username, layername=layername)
    with layman.app_context():
        rv = client.delete(rest_path)
    assert rv.status_code == 404
    resp_json = rv.get_json()
    assert resp_json['code'] == 15

def test_get_layers_empty_again(client):
    username = 'testuser2'
    with layman.app_context():
        rv = client.get(url_for('get_layers', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 0

