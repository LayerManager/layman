import pytest
import os

from .layman import app as layman
from .settings import LAYMAN_DATA_PATH

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
    assert resp_json['data']['parameter']=='user'


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
        assert resp_json['data']['parameter']=='user'


def test_no_file(client):
    rv = client.post('/layers', data={
        'user': 'testuser1'
    })
    assert rv.status_code==400
    resp_json = rv.get_json()
    # print(resp_json)
    assert resp_json['code']==1
    assert resp_json['data']['parameter']=='file'


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
    for fp in file_paths:
        assert os.path.isfile(os.path.join(
            LAYMAN_DATA_PATH, username, os.path.basename(fp)))
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
