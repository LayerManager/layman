import pytest
import io

from .layman import app as layman
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
    client = layman.test_client()

    with layman.app_context():
        pass

    yield client

def test_no_user(client):
    rv = client.post('/layers')
    assert rv.status_code==400
    resp_json = rv.get_json()
    # print(resp_json)
    assert resp_json['code']==1
    assert resp_json['detail']['parameter']=='user'


def test_wrong_value_of_user(client):
    usernames = ['', ' ', '2a', 'ě', ';', '?', 'ABC']
    for username in usernames:
        rv = client.post('/layers', data={
            'user': username
        })
        assert rv.status_code==400
        resp_json = rv.get_json()
        # print(resp_json)
        assert resp_json['code']==2
        assert resp_json['detail']['parameter']=='user'


def test_no_file(client):
    rv = client.post('/layers', data={
        'user': 'testuser1'
    })
    assert rv.status_code==400
    resp_json = rv.get_json()
    # print('resp_json', resp_json)
    assert resp_json['code']==1
    assert resp_json['detail']['parameter']=='file'


def test_username_schema_conflict(client):
    if len(PG_NON_USER_SCHEMAS) == 0:
        pass
    rv = client.post('/layers', data={
        'user': PG_NON_USER_SCHEMAS[0]
    })
    assert rv.status_code==409
    resp_json = rv.get_json()
    # print(resp_json)
    assert resp_json['code']==8
    for schema_name in [
        'pg_catalog',
        'pg_toast',
        'information_schema',
    ]:
        rv = client.post('/layers', data={
            'user': schema_name,
            'file': [
                (io.BytesIO(min_geojson.encode()), '/file.geojson')
            ]
        })
        resp_json = rv.get_json()
        # print(resp_json)
        assert rv.status_code==409
        assert resp_json['code']==10


def test_file_upload(client):
    username = 'testuser1'
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
        rv = client.post('/layers', data={
            'user': username,
            'file': files
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()
    from .gs_util import wms_proxy
    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert 'ne_110m_admin_0_countries' in wms.contents

    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post('/layers', data={
            'user': username,
            'file': files
        })
        assert rv.status_code==409
        resp_json = rv.get_json()
        assert resp_json['code']==3
    finally:
        for fp in files:
            fp[0].close()

    username = 'testuser2'
    sld_path = 'sample/style/generic-blue.xml'
    assert os.path.isfile(sld_path)
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post('/layers', data={
            'user': username,
            'file': files,
            'title': 'staty',
            'description': 'popis států',
            'sld': (open(sld_path, 'rb'), os.path.basename(sld_path)),
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()
    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    wms = wms_proxy(wms_url)
    assert 'ne_110m_admin_0_countries' in wms.contents
    assert wms['ne_110m_admin_0_countries'].title == 'staty'
    assert wms['ne_110m_admin_0_countries'].abstract == 'popis států'
    assert wms['ne_110m_admin_0_countries'].styles[
        username+':ne_110m_admin_0_countries']['title'] == 'Generic Blue'


def test_layername_db_object_conflict(client):
    username = 'testuser1'
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
        rv = client.post('/layers', data={
            'user': username,
            'file': files,
            'name': 'spatial_ref_sys'
        })
        assert rv.status_code == 409
        resp_json = rv.get_json()
        assert resp_json['code']==9
    finally:
        for fp in files:
            fp[0].close()
