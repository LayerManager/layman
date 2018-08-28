import io

import pytest
from flask import url_for

from layman import app as layman
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


def test_get_layers_empty(client):
    username = 'testuser1'
    with layman.app_context():
        rv = client.get(url_for('get_layers', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 0


def test_file_upload(client):
    username = 'testuser1'
    rest_path = url_for('post_layers', username=username)
    file_paths = [
        # 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.cpg',
        # 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.dbf',
        # 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.prj',
        # 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.README.html',
        # 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp',
        # 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shx',
        # 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.VERSION.txt',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
        assert not os.path.isfile(os.path.join(LAYMAN_DATA_PATH,
                                               os.path.basename(fp)))
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
    from layman.geoserver.util import wms_proxy
    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert 'ne_110m_admin_0_countries' in wms.contents

    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        with layman.app_context():
            rv = client.post(rest_path, data={
                'file': files
            })
        assert rv.status_code==409
        resp_json = rv.get_json()
        assert resp_json['code']==3
    finally:
        for fp in files:
            fp[0].close()

    username = 'testuser2'
    rest_path = url_for('post_layers', username=username)
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


def test_get_layers(client):
    username = 'testuser1'
    with layman.app_context():
        rv = client.get(url_for('get_layers', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 1
    assert resp_json[0]['name'] == 'ne_110m_admin_0_countries'

    username = 'testuser2'
    with layman.app_context():
        rv = client.get(url_for('get_layers', username=username))
    resp_json = rv.get_json()
    assert rv.status_code==200
    assert len(resp_json) == 1
    assert resp_json[0]['name'] == 'countries'


def test_layername_db_object_conflict(client):
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
        assert not os.path.isfile(os.path.join(LAYMAN_DATA_PATH,
                                               os.path.basename(fp)))
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
