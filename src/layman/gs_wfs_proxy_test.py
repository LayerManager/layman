import pytest
import requests
from owslib.feature.schema import get_schema as get_wfs_schema

from layman import app
from layman import settings
from layman.layer import db
from test.process_client import get_authz_headers
from test import process_client as client_util, geoserver_client
from test.data import wfs as data_wfs
from layman.layer.geoserver import wfs as geoserver_wfs
from layman.common.geoserver import get_layer_thumbnail, get_layer_square_bbox


@pytest.mark.usefixtures('ensure_layman')
def test_rest_get():
    username = 'wfs_proxy_test'
    layername = 'layer_wfs_proxy_test'

    client_util.publish_layer(username, layername)

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs?request=Transaction"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    data_xml = data_wfs.get_wfs20_insert_points(username, layername)

    with app.app_context():
        r = requests.post(rest_url,
                          data=data_xml,
                          headers=headers)
    assert r.status_code == 200, r.text

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=GetCapabilities"
    with app.app_context():
        r = requests.post(rest_url,
                          headers=headers)
    assert r.status_code == 200

    client_util.delete_layer(username, layername)


def setup_user_layer(username, layername, authn_headers):
    client_util.reserve_username(username, headers=authn_headers)
    ln = client_util.publish_layer(username, layername, [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ], headers=authn_headers)

    assert ln == layername


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_wfs_proxy():
    username = 'testproxy'
    layername1 = 'ne_countries'
    username2 = 'testproxy2'

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


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
@pytest.mark.parametrize('service_endpoint', ['ows', 'wms'])
def test_wms_ows_proxy(service_endpoint):
    username = 'test_wms_ows_proxy_user'
    layername = 'test_wms_ows_proxy_layer'

    authn_headers = get_authz_headers(username)

    client_util.ensure_reserved_username(username, headers=authn_headers)
    ln = client_util.publish_layer(username, layername, headers=authn_headers)

    assert ln == layername

    wms_url = geoserver_client.get_wms_url(username, service_endpoint)

    wms = geoserver_client.get_wms_capabilities(username, service_endpoint, headers=authn_headers)

    # current_app.logger.info(list(wms.contents))
    tn_bbox = get_layer_square_bbox(wms, layername)

    from layman.layer.geoserver.wms import VERSION
    r = get_layer_thumbnail(wms_url, layername, tn_bbox, headers=authn_headers, wms_version=VERSION)
    r.raise_for_status()
    assert 'image' in r.headers['content-type']

    client_util.delete_layer(username, layername, headers=authn_headers)


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_missing_attribute():
    username = 'testmissingattr'
    layername = 'inexisting_attribute_layer'
    layername2 = 'inexisting_attribute_layer2'

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

    wfs_t_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=Transaction"

    def wfs_post(username, attr_names_list, data_xml):
        with app.app_context():
            wfs_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs"
            old_db_attributes = {}
            old_wfs_properties = {}
            for layername, attr_names in attr_names_list:
                # test that all attr_names are not yet presented in DB table
                old_db_attributes[layername] = db.get_all_column_names(username, layername)
                for attr_name in attr_names:
                    assert attr_name not in old_db_attributes[layername], f"old_db_attributes={old_db_attributes[layername]}, attr_name={attr_name}"
                layer_schema = get_wfs_schema(
                    wfs_url, typename=f"{username}:{layername}", version=geoserver_wfs.VERSION, headers=authn_headers)
                old_wfs_properties[layername] = sorted(layer_schema['properties'].keys())

            r = requests.post(wfs_t_url,
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
                layer_schema = get_wfs_schema(
                    wfs_url, typename=f"{username}:{layername}", version=geoserver_wfs.VERSION, headers=authn_headers)
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


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_missing_attribute_authz():
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
