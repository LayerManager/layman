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
    usernames = ['', ' ', '2a', 'ě', ';', '?']
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
        'user': 'abcd'
    })
    assert rv.status_code==400
    resp_json = rv.get_json()
    # print(resp_json)
    assert resp_json['code']==1
    assert resp_json['data']['parameter']=='file'


def test_file_upload(client):
    file_paths = ['sample/data/stations.geojson']
    for fp in file_paths:
        assert os.path.isfile(fp)
        assert not os.path.isfile(os.path.join(LAYMAN_DATA_PATH,
                                               os.path.basename(fp)))
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        client.post('/layers', data={
            'user': 'abcd',
            'file': files
        })
    finally:
        for fp in files:
            fp[0].close()
    for fp in file_paths:
        assert os.path.isfile(os.path.join(LAYMAN_DATA_PATH, os.path.basename(
                                                   fp)))
