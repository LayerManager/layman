from multiprocessing import Process
import requests
import time
from flask import url_for
import pytest
from urllib.parse import urljoin

import sys
import os

del sys.modules['layman']

from layman import app
from layman import settings
from layman.layer.rest_test import wait_till_ready
from layman.layer import db
from test import process, client as client_util
from layman.layer.geoserver.util import wfs_proxy

liferay_mock = process.liferay_mock

LIFERAY_PORT = process.LIFERAY_PORT

ISS_URL_HEADER = client_util.ISS_URL_HEADER
TOKEN_HEADER = client_util.TOKEN_HEADER

AUTHN_INTROSPECTION_URL = process.AUTHN_INTROSPECTION_URL
AUTHN_SETTINGS = process.AUTHN_SETTINGS


@pytest.fixture()
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

    yield client

    server.terminate()
    server.join()


def test_rest_get(client):
    username = 'wfs_proxy_test'
    layername = 'layer_wfs_proxy_test'

    setup_layer_flask(username, layername, client)

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs?request=Transaction"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    data_xml = client_util.get_wfs_insert_points(username, layername)

    with app.app_context():
        r = client.post(rest_url,
                        data=data_xml,
                        headers=headers)
    assert r.status_code == 200

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=GetCapabilities"
    with app.app_context():
        r = client.post(rest_url,
                        headers=headers)
    assert r.status_code == 200

    with app.app_context():
        rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
        client.delete(rest_path)
        assert r.status_code == 200


def get_auth_header(username, iss_url_header, token_header):
    return {f'{iss_url_header}': 'http://localhost:8082/o/oauth2/authorize',
            f'{token_header}': f'Bearer {username}',
            }


def setup_user_layer(username, layername, authn_headers):
    client_util.reserve_username(username, headers=authn_headers)
    ln = client_util.publish_layer(username, layername, [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ], headers=authn_headers)

    assert ln == layername


def test_wfs_proxy(liferay_mock):
    username = 'testproxy'
    layername1 = 'ne_countries'
    username2 = 'testproxy2'

    layman_process = process.start_layman(dict({
        'LAYMAN_AUTHZ_MODULE': 'layman.authz.read_everyone_write_owner',
    }, **AUTHN_SETTINGS))

    authn_headers1 = get_auth_header(username, ISS_URL_HEADER, TOKEN_HEADER)

    setup_user_layer(username, layername1, authn_headers1)

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs?request=Transaction"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        **authn_headers1,
    }

    data_xml = client_util.get_wfs_insert_points(username, layername1)

    r = requests.post(rest_url,
                      data=data_xml,
                      headers=headers)
    assert r.status_code == 200, r.text

    # Testing, that user1 is able to write his own layer through general WFS endpoint
    general_rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=Transaction"
    r = requests.post(general_rest_url,
                      data=data_xml,
                      headers=headers)
    assert r.status_code == 200, r.text

    # Testing, that user2 is not able to write to layer of user1
    authn_headers2 = get_auth_header(username2, ISS_URL_HEADER, TOKEN_HEADER)

    headers2 = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        **authn_headers2,
    }

    client_util.reserve_username(username2, headers=authn_headers2)

    r = requests.post(rest_url,
                      data=data_xml,
                      headers=headers2)
    assert r.status_code == 400, r.text

    # Testing, that user2 is not able to write user1's layer through general WFS endpoint
    general_rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=Transaction"
    r = requests.post(general_rest_url,
                      data=data_xml,
                      headers=headers2)
    assert r.status_code == 400, r.text

    # Test anonymous
    headers3 = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    r = requests.post(rest_url,
                      data=data_xml,
                      headers=headers3)
    assert r.status_code == 400, r.text

    # Test fraud header
    headers4 = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: username,
    }

    r = requests.post(rest_url,
                      data=data_xml,
                      headers=headers4)
    assert r.status_code == 400, r.text

    process.stop_process(layman_process)


def setup_layer_flask(username, layername, client):
    with app.app_context():
        rest_path = url_for('rest_layers.post', username=username)

        file_paths = [
            'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson',
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

    wait_till_ready(username, layername)


def test_missing_attribute(client):
    username = 'testmissingattr'
    layername = 'inexisting_attribute_layer'
    attr_names = ['inexisting_attribute_attr', 'inexisting_attribute_attr1a']

    setup_layer_flask(username, layername, client)

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=Transaction"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    def wfs_post(username, layername, data_xml, attr_names):
        with app.app_context():
            old_attributes = db.get_all_column_names(username, layername)
            for attr_name in attr_names:
                assert attr_name not in old_attributes, f"old_attributes={old_attributes}, attr_name={attr_name}"

            r = client.post(rest_url,
                            data=data_xml,
                            headers=headers)
            assert r.status_code == 200, f"{r.get_data()}"
            new_attributes = db.get_all_column_names(username, layername)
            for attr_name in attr_names:
                assert attr_name in new_attributes, f"new_attributes={new_attributes}, attr_name={attr_name}"
            assert set(attr_names).union(set(old_attributes)) == set(new_attributes)

            wfs_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
            wfs = wfs_proxy(wfs_url)
            assert f"{username}:{layername}" in wfs.contents
            layer_schema = wfs.get_schema(f"{username}:{layername}")
            new_wfs_properties = sorted(layer_schema['properties'].keys())
            for attr_name in attr_names:
                assert attr_name in new_wfs_properties, f"new_wfs_properties={new_wfs_properties}, attr_name={attr_name}"

    data_xml = client_util.get_wfs_insert_points_new_attr(username, layername, attr_names)
    wfs_post(username, layername, data_xml, attr_names)

    attr_names2 = ['inexisting_attribute_attr2']
    data_xml = client_util.get_wfs_update_points_new_attr(username, layername, attr_names2)
    wfs_post(username, layername, data_xml, attr_names2)

    attr_names3 = ['inexisting_attribute_attr3']
    data_xml = client_util.get_wfs_update_points_new_attr(username, layername, attr_names3, with_attr_namespace=True)
    wfs_post(username, layername, data_xml, attr_names3)

    attr_names4 = ['inexisting_attribute_attr4']
    data_xml = client_util.get_wfs_update_points_new_attr(username, layername, attr_names4, with_filter=True)
    wfs_post(username, layername, data_xml, attr_names4)

    attr_names5 = ['inexisting_attribute_attr5']
    data_xml = client_util.get_wfs_replace_points_new_attr(username, layername, attr_names5)
    wfs_post(username, layername, data_xml, attr_names5)
