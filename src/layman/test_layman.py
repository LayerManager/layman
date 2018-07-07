import pytest

from .layman import app as layman


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
    print(resp_json)
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
        print(resp_json)
        assert resp_json['code']==2
        assert resp_json['data']['parameter']=='user'


def test_no_file(client):
    rv = client.post('/layers', data={
        'user': 'abcd'
    })
    assert rv.status_code==400
    resp_json = rv.get_json()
    print(resp_json)
    assert resp_json['code']==1
    assert resp_json['data']['parameter']=='file'
