import pytest

from geoserver.error import Error as GS_Error
from layman import app
from layman.layer import db
from test_tools import process_client
from test_tools.data import wfs as data_wfs
from test_tools.process_client import get_authz_headers


def setup_user_layer(username, layername, authn_headers):
    process_client.reserve_username(username, headers=authn_headers)
    process_client.publish_workspace_layer(username, layername, file_paths=[
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ], headers=authn_headers)


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_missing_attribute_authz():
    username = 'testmissingattr_authz'
    layername1 = 'testmissingattr_authz_layer'
    username2 = 'testmissingattr_authz2'

    authn_headers1 = get_authz_headers(username)
    authn_headers2 = get_authz_headers(username2)

    def do_test(wfs_query, attribute_names):
        # Test, that unauthorized user will not cause new attribute
        with app.app_context():
            old_db_attributes = db.get_all_column_names(username, layername1)
        for attr_name in attribute_names:
            assert attr_name not in old_db_attributes, f"old_db_attributes={old_db_attributes}, attr_name={attr_name}"
        with pytest.raises(GS_Error) as exc:
            process_client.post_wfst(wfs_query, headers=authn_headers2, workspace=username)
        assert exc.value.data['status_code'] == 400

        with app.app_context():
            new_db_attributes = db.get_all_column_names(username, layername1)
        for attr_name in attribute_names:
            assert attr_name not in new_db_attributes, f"new_db_attributes={new_db_attributes}, attr_name={attr_name}"

        # Test, that authorized user will cause new attribute
        process_client.post_wfst(wfs_query, headers=authn_headers1, workspace=username)
        with app.app_context():
            new_db_attributes = db.get_all_column_names(username, layername1)
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
