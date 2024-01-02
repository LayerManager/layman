import pytest

from geoserver.error import Error as GS_Error
from layman import app
from layman.layer import db
from test_tools import process_client
from test_tools.data import wfs as data_wfs
from test_tools.process_client import get_authz_headers
from . import geoserver_proxy


@pytest.mark.usefixtures('ensure_layman', 'oauth2_provider_mock')
def test_missing_attribute_authz():
    username = 'testmissingattr_authz'
    layername1 = 'testmissingattr_authz_layer'
    username2 = 'testmissingattr_authz2'

    authn_headers1 = get_authz_headers(username)
    authn_headers2 = get_authz_headers(username2)

    def do_test(wfs_query, attribute_names):
        # Test, that unauthorized user will not cause new attribute
        with app.app_context():
            old_db_attributes = db.get_internal_table_all_column_names(username, layername1)
        for attr_name in attribute_names:
            assert attr_name not in old_db_attributes, f"old_db_attributes={old_db_attributes}, attr_name={attr_name}"
        with pytest.raises(GS_Error) as exc:
            process_client.post_wfst(wfs_query, headers=authn_headers2, workspace=username)
        assert exc.value.data['status_code'] == 400

        with app.app_context():
            new_db_attributes = db.get_internal_table_all_column_names(username, layername1)
        for attr_name in attribute_names:
            assert attr_name not in new_db_attributes, f"new_db_attributes={new_db_attributes}, attr_name={attr_name}"

        # Test, that authorized user will cause new attribute
        process_client.post_wfst(wfs_query, headers=authn_headers1, workspace=username)
        with app.app_context():
            new_db_attributes = db.get_internal_table_all_column_names(username, layername1)
        for attr_name in attribute_names:
            assert attr_name in new_db_attributes, f"new_db_attributes={new_db_attributes}, attr_name={attr_name}"

    process_client.reserve_username(username, headers=authn_headers1)
    process_client.publish_workspace_layer(username,
                                           layername1,
                                           file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson', ],
                                           headers=authn_headers1)

    # Testing, that user2 is not able to write to layer of user1
    process_client.reserve_username(username2, headers=authn_headers2)

    # INSERT
    attr_names = ['inexisting_attribute_auth1', 'inexisting_attribute_auth2']
    data_xml = data_wfs.get_wfs20_insert_points_new_attr(username, layername1, attr_names)
    do_test(data_xml, attr_names)

    # UPDATE
    attr_names = ['inexisting_attribute_auth3', 'inexisting_attribute_auth4']
    data_xml = data_wfs.get_wfs20_update_points_new_attr(username, layername1, attr_names)
    do_test(data_xml, attr_names)

    process_client.delete_workspace_layer(username, layername1, headers=authn_headers1)


@pytest.mark.parametrize('wfst_data_method, hardcoded_attrs', [
    pytest.param(
        data_wfs.get_wfs20_insert_points_new_attr,
        ['wkb_geometry', 'name', 'labelrank'],
        id='insert',
    ),
    pytest.param(
        data_wfs.get_wfs20_replace_points_new_attr,
        ['wkb_geometry', 'name', 'labelrank'],
        id='replace',
    ),
    pytest.param(
        data_wfs.get_wfs20_update_points_new_attr,
        [],
        id='update',
    ),
])
def test_extract_attributes_and_layers_from_wfs_t(wfst_data_method, hardcoded_attrs):
    workspace = 'workspace_name'
    layer = 'layer_name'
    new_attrs = ['ok_attr', 'dangerous-attr-with-dashes']
    data_xml = wfst_data_method(workspace, layer, new_attrs)
    with app.app_context():
        extracted_attribs, extracted_layers = geoserver_proxy.extract_attributes_and_layers_from_wfs_t(data_xml)

    exp_attrs = {*new_attrs, *hardcoded_attrs}
    assert extracted_layers == {(workspace, layer)}
    assert extracted_attribs == {(workspace, layer, attr) for attr in exp_attrs}


@pytest.mark.parametrize('wfst_data_method, exp_attributes_and_layers', [
    pytest.param(
        data_wfs.get_wfs11_implicit_ns_update,
        ({('filip', 'poly', 'wkb_geometry')}, {('filip', 'poly')}),
        id='update_wfs1',
    ),
    pytest.param(
        data_wfs.get_wfs2_implicit_ns_update,
        ({('filip', 'poly', 'wkb_geometry')}, {('filip', 'poly')}),
        id='update_wfs2',
    ),
    pytest.param(
        data_wfs.get_wfs1_implicit_ns_delete,
        (set(), {('filip', 'europa_5514')}),
        id='delete_wfs1',
    ),
    pytest.param(
        data_wfs.get_wfs1_implicit_ns_insert,
        ({('filip', 'europa_5514', 'scalerank'), ('filip', 'europa_5514', 'featurecla'), ('filip', 'europa_5514', 'sovereignt'), ('filip', 'europa_5514', 'wkb_geometry'), ('filip', 'europa_5514', 'name'), ('filip', 'europa_5514', 'labelrank')}, {('filip', 'europa_5514')}),
        id='insert_wfs1',
    ),
])
def test_extract_attributes_and_layers_from_wfs_t_implicit_ws(wfst_data_method, exp_attributes_and_layers):
    binary_data = wfst_data_method()
    with app.app_context():
        attributes_and_layers = geoserver_proxy.extract_attributes_and_layers_from_wfs_t(binary_data)
    assert attributes_and_layers == exp_attributes_and_layers
