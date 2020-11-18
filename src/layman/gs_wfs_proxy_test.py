import requests
from urllib.parse import urljoin

from layman import app
from layman import settings
from layman.layer import db
from test.process_client import get_authz_headers
from test import process, process_client as client_util, flask_client
from test.data import wfs as data_wfs
from layman.layer.geoserver.util import wfs_proxy

liferay_mock = process.liferay_mock

LIFERAY_PORT = process.LIFERAY_PORT

ISS_URL_HEADER = client_util.ISS_URL_HEADER
TOKEN_HEADER = client_util.TOKEN_HEADER

AUTHN_INTROSPECTION_URL = process.AUTHN_INTROSPECTION_URL
AUTHN_SETTINGS = process.AUTHN_SETTINGS


client = flask_client.client


def test_rest_get(client):
    username = 'wfs_proxy_test'
    layername = 'layer_wfs_proxy_test'

    flask_client.publish_layer(username, layername, client)

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs?request=Transaction"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    data_xml = data_wfs.get_wfs20_insert_points(username, layername)

    with app.app_context():
        r = client.post(rest_url,
                        data=data_xml,
                        headers=headers)
    assert r.status_code == 200, r.data

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=GetCapabilities"
    with app.app_context():
        r = client.post(rest_url,
                        headers=headers)
    assert r.status_code == 200

    flask_client.delete_layer(username, layername, client)


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

    layman_process = process.start_layman(dict({'LAYMAN_AUTHZ_MODULE': 'layman.authz.read_everyone_write_owner', },
                                               **AUTHN_SETTINGS))

    authn_headers1 = get_authz_headers(username)

    client_util.reserve_username(username, headers=authn_headers1)
    ln = client_util.publish_layer(username,
                                   layername1,
                                   headers=authn_headers1)

    assert ln == layername1

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs?request=Transaction"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        **authn_headers1,
    }

    data_xml = data_wfs.get_wfs20_insert_points(username, layername1)

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
    authn_headers2 = get_authz_headers(username2)

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

    client_util.delete_layer(username, layername1, headers)

    process.stop_process(layman_process)


def test_missing_attribute(liferay_mock):
    username = 'testmissingattr'
    layername = 'inexisting_attribute_layer'
    layername2 = 'inexisting_attribute_layer2'

    layman_process = process.start_layman(AUTHN_SETTINGS)
    authn_headers = get_authz_headers(username)
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        **authn_headers,
    }

    client_util.reserve_username(username, headers=authn_headers)
    ln = client_util.publish_layer(username,
                                   layername,
                                   ['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson', ],
                                   headers=authn_headers,
                                   )
    assert ln == layername
    ln2 = client_util.publish_layer(username,
                                    layername2,
                                    ['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson', ],
                                    headers=authn_headers,
                                    )
    assert ln2 == layername2

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=Transaction"

    def wfs_post(username, attr_names_list, data_xml):
        with app.app_context():
            wfs_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
            old_db_attributes = {}
            old_wfs_properties = {}
            for layername, attr_names in attr_names_list:
                # test that all attr_names are not yet presented in DB table
                old_db_attributes[layername] = db.get_all_column_names(username, layername)
                for attr_name in attr_names:
                    assert attr_name not in old_db_attributes[layername], f"old_db_attributes={old_db_attributes[layername]}, attr_name={attr_name}"
                wfs = wfs_proxy(wfs_url)
                layer_schema = wfs.get_schema(f"{username}:{layername}")
                old_wfs_properties[layername] = sorted(layer_schema['properties'].keys())

            r = requests.post(rest_url,
                              data=data_xml,
                              headers=headers)
            assert r.status_code == 200, f"r.status_code={r.status_code}\n{r.text}"

            new_db_attributes = {}
            new_wfs_properties = {}
            for layername, attr_names in attr_names_list:
                # test that exactly all attr_names were created in DB table
                new_db_attributes[layername] = db.get_all_column_names(username, layername)
                for attr_name in attr_names:
                    assert attr_name in new_db_attributes[layername], f"new_db_attributes={new_db_attributes[layername]}, attr_name={attr_name}"
                assert set(attr_names).union(set(old_db_attributes[layername])) == set(new_db_attributes[layername])

                # test that exactly all attr_names were distinguished also in WFS feature type
                wfs = wfs_proxy(wfs_url)
                layer_schema = wfs.get_schema(f"{username}:{layername}")
                new_wfs_properties[layername] = sorted(layer_schema['properties'].keys())
                for attr_name in attr_names:
                    assert attr_name in new_wfs_properties[layername], f"new_wfs_properties={new_wfs_properties[layername]}, attr_name={attr_name}"
                assert set(attr_names).union(set(old_wfs_properties[layername])) == set(new_wfs_properties[layername]),\
                    set(new_wfs_properties[layername]).difference(set(attr_names).union(set(old_wfs_properties[layername])))

    attr_names = ['inexisting_attribute_attr', 'inexisting_attribute_attr1a']
    data_xml = data_wfs.get_wfs20_insert_points_new_attr(username, layername, attr_names)
    wfs_post(username, [(layername, attr_names)], data_xml)

    attr_names2 = ['inexisting_attribute_attr2']
    data_xml = data_wfs.get_wfs20_update_points_new_attr(username, layername, attr_names2)
    wfs_post(username, [(layername, attr_names2)], data_xml)

    attr_names3 = ['inexisting_attribute_attr3']
    data_xml = data_wfs.get_wfs20_update_points_new_attr(username, layername, attr_names3, with_attr_namespace=True)
    wfs_post(username, [(layername, attr_names3)], data_xml)

    attr_names4 = ['inexisting_attribute_attr4']
    data_xml = data_wfs.get_wfs20_update_points_new_attr(username, layername, attr_names4, with_filter=True)
    wfs_post(username, [(layername, attr_names4)], data_xml)

    attr_names5 = ['inexisting_attribute_attr5']
    data_xml = data_wfs.get_wfs20_replace_points_new_attr(username, layername, attr_names5)
    wfs_post(username, [(layername, attr_names5)], data_xml)

    attr_names_i1 = ['inexisting_attribute_attr_complex_i1']
    attr_names_i2 = ['inexisting_attribute_attr_complex_i2']
    attr_names_u = ['inexisting_attribute_attr_complex_u']
    attr_names_r = ['inexisting_attribute_attr_complex_r']
    attr_names_complex = [(layername, attr_names_i1 + attr_names_r), (layername2, attr_names_i2 + attr_names_u)]
    data_xml = data_wfs.get_wfs20_complex_new_attr(username=username,
                                                   layername1=layername,
                                                   layername2=layername2,
                                                   attr_names_insert1=attr_names_i1,
                                                   attr_names_insert2=attr_names_i2,
                                                   attr_names_update=attr_names_u,
                                                   attr_names_replace=attr_names_r
                                                   )
    wfs_post(username, attr_names_complex, data_xml)

    attr_names6 = ['inexisting_attribute_attr6']
    data_xml = data_wfs.get_wfs10_insert_points_new_attr(username, layername, attr_names6)
    wfs_post(username, [(layername, attr_names6)], data_xml)

    attr_names7 = ['inexisting_attribute_attr7']
    data_xml = data_wfs.get_wfs11_insert_points_new_attr(username, layername, attr_names7)
    wfs_post(username, [(layername, attr_names7)], data_xml)

    attr_names8 = ['inexisting_attribute_attr8']
    data_xml = data_wfs.get_wfs10_update_points_new(username, layername, attr_names8, with_attr_namespace=True)
    wfs_post(username, [(layername, attr_names8)], data_xml)

    attr_names9 = ['inexisting_attribute_attr9']
    data_xml = data_wfs.get_wfs10_update_points_new(username, layername, attr_names9, with_filter=True)
    wfs_post(username, [(layername, attr_names9)], data_xml)

    attr_names10 = ['inexisting_attribute_attr10']
    data_xml = data_wfs.get_wfs11_insert_polygon_new_attr(username, layername, attr_names10)
    wfs_post(username, [(layername, attr_names10)], data_xml)

    client_util.delete_layer(username, layername, headers)
    client_util.delete_layer(username, layername2, headers)

    process.stop_process(layman_process)


def test_missing_attribute_authz(liferay_mock):
    username = 'testmissingattr_authz'
    layername1 = 'testmissingattr_authz_layer'
    username2 = 'testmissingattr_authz2'

    authn_headers1 = get_authz_headers(username)
    authn_headers2 = get_authz_headers(username2)
    headers1 = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        **authn_headers1,
    }
    headers2 = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        **authn_headers2,
    }

    def do_test(wfs_query, attribute_names):
        # Test, that unauthorized user will not cause new attribute
        with app.app_context():
            old_db_attributes = db.get_all_column_names(username, layername1)
        for attr_name in attribute_names:
            assert attr_name not in old_db_attributes, f"old_db_attributes={old_db_attributes}, attr_name={attr_name}"
        r = requests.post(rest_url,
                          data=wfs_query,
                          headers=headers2)
        assert r.status_code == 400, r.text
        with app.app_context():
            new_db_attributes = db.get_all_column_names(username, layername1)
        for attr_name in attribute_names:
            assert attr_name not in new_db_attributes, f"new_db_attributes={new_db_attributes}, attr_name={attr_name}"

        # Test, that authorized user will cause new attribute
        r = requests.post(rest_url,
                          data=wfs_query,
                          headers=headers1)
        assert r.status_code == 200, r.text
        with app.app_context():
            new_db_attributes = db.get_all_column_names(username, layername1)
        for attr_name in attribute_names:
            assert attr_name in new_db_attributes, f"new_db_attributes={new_db_attributes}, attr_name={attr_name}"

    layman_process = process.start_layman(dict({
        'LAYMAN_AUTHZ_MODULE': 'layman.authz.read_everyone_write_owner',
    }, **AUTHN_SETTINGS))

    client_util.reserve_username(username, headers=authn_headers1)
    ln = client_util.publish_layer(username,
                                   layername1,
                                   ['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson', ],
                                   headers=authn_headers1)
    assert ln == layername1

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs?request=Transaction"

    # Testing, that user2 is not able to write to layer of user1

    client_util.reserve_username(username2, headers=authn_headers2)

    # INSERT
    attr_names = ['inexisting_attribute_auth1', 'inexisting_attribute_auth2']
    data_xml = data_wfs.get_wfs20_insert_points_new_attr(username, layername1, attr_names)
    do_test(data_xml, attr_names)

    # UPDATE
    attr_names = ['inexisting_attribute_auth3', 'inexisting_attribute_auth4']
    data_xml = data_wfs.get_wfs20_update_points_new_attr(username, layername1, attr_names)
    do_test(data_xml, attr_names)

    client_util.delete_layer(username, layername1, headers1)

    process.stop_process(layman_process)
