from owslib.feature.schema import get_schema as get_wfs_schema
import pytest

from geoserver.error import Error as GS_Error
from layman import app, settings, util as layman_util
from layman.layer import db
from layman.layer.filesystem import thumbnail
from layman.layer.geoserver import wfs as geoserver_wfs
from layman.layer.qgis import util as qgis_util, wms as qgis_wms
from test_tools import process_client, util as test_util, assert_util
from test_tools.data import wfs as data_wfs, SMALL_LAYER_BBOX, SMALL_LAYER_NATIVE_BBOX, SMALL_LAYER_NATIVE_CRS
from test_tools.process_client import get_authz_headers


def setup_user_layer(username, layername, authn_headers):
    process_client.reserve_username(username, headers=authn_headers)
    process_client.publish_workspace_layer(username, layername, file_paths=[
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ], headers=authn_headers)


@pytest.mark.timeout(60)
@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
@pytest.mark.parametrize('style_file', [
    None,
    'sample/style/ne_10m_admin_0_countries.qml',
])
def test_missing_attribute(style_file, ):
    username = 'testmissingattr'
    layername = 'inexisting_attribute_layer'
    layername2 = 'inexisting_attribute_layer2'

    authn_headers = get_authz_headers(username)

    process_client.ensure_reserved_username(username, headers=authn_headers)
    process_client.publish_workspace_layer(username,
                                           layername,
                                           file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson', ],
                                           style_file=style_file,
                                           headers=authn_headers,
                                           )
    process_client.publish_workspace_layer(username,
                                           layername2,
                                           file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson', ],
                                           style_file=style_file,
                                           headers=authn_headers,
                                           )

    with app.app_context():
        style_type = layman_util.get_publication_info(username, process_client.LAYER_TYPE, layername, context={'keys': ['style_type'], })['_style_type']

    def wfs_post(workspace, attr_names_list, data_xml):
        with app.app_context():
            wfs_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{workspace}/wfs"
            old_db_attributes = {}
            old_wfs_properties = {}
            for layer, attr_names in attr_names_list:
                # test that all attr_names are not yet presented in DB table
                old_db_attributes[layer] = db.get_all_column_names(workspace, layer)
                for attr_name in attr_names:
                    assert attr_name not in old_db_attributes[layer], f"old_db_attributes={old_db_attributes[layer]}, attr_name={attr_name}"
                layer_schema = get_wfs_schema(
                    wfs_url, typename=f"{workspace}:{layer}", version=geoserver_wfs.VERSION, headers=authn_headers)
                old_wfs_properties[layer] = sorted(layer_schema['properties'].keys())
                if style_type == 'qml':
                    assert qgis_wms.get_layer_info(workspace, layer)
                    old_qgis_attributes = qgis_util.get_layer_attribute_names(workspace, layer)
                    assert all(attr_name not in old_qgis_attributes for attr_name in attr_names), (attr_names, old_qgis_attributes)

            process_client.post_wfst(data_xml, headers=authn_headers, workspace=username)

            new_db_attributes = {}
            new_wfs_properties = {}
            for layer, attr_names in attr_names_list:
                # test that exactly all attr_names were created in DB table
                new_db_attributes[layer] = db.get_all_column_names(workspace, layer)
                for attr_name in attr_names:
                    assert attr_name in new_db_attributes[layer], f"new_db_attributes={new_db_attributes[layer]}, attr_name={attr_name}"
                assert set(attr_names).union(set(old_db_attributes[layer])) == set(new_db_attributes[layer])

                # test that exactly all attr_names were distinguished also in WFS feature type
                layer_schema = get_wfs_schema(
                    wfs_url, typename=f"{workspace}:{layer}", version=geoserver_wfs.VERSION, headers=authn_headers)
                new_wfs_properties[layer] = sorted(layer_schema['properties'].keys())
                for attr_name in attr_names:
                    assert attr_name in new_wfs_properties[layer], f"new_wfs_properties={new_wfs_properties[layer]}, attr_name={attr_name}"
                assert set(attr_names).union(set(old_wfs_properties[layer])) == set(new_wfs_properties[layer]),\
                    set(new_wfs_properties[layer]).difference(set(attr_names).union(set(old_wfs_properties[layer])))
                if style_type == 'qml':
                    assert qgis_wms.get_layer_info(workspace, layer)
                    new_qgis_attributes = qgis_util.get_layer_attribute_names(workspace, layer)
                    assert all(attr_name in new_qgis_attributes for attr_name in attr_names), (attr_names, new_qgis_attributes)
                else:
                    assert not qgis_wms.get_layer_info(workspace, layer)

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
    data_xml = data_wfs.get_wfs20_complex_new_attr(workspace=username,
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

    process_client.delete_workspace_layer(username, layername, headers=authn_headers)
    process_client.delete_workspace_layer(username, layername2, headers=authn_headers)


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


@pytest.mark.parametrize('style_file, thumbnail_style_postfix', [
    (None, '_sld'),
    ('sample/style/small_layer.qml', '_qml'),
])
@pytest.mark.usefixtures('ensure_layman')
def test_wfs_bbox(style_file, thumbnail_style_postfix):
    workspace = 'test_wfs_bbox_workspace'
    layer = 'test_wfs_bbox_layer'

    process_client.publish_workspace_layer(workspace, layer, style_file=style_file, )

    native_crs = SMALL_LAYER_NATIVE_CRS
    assert_util.assert_all_sources_bbox(workspace, layer, SMALL_LAYER_BBOX,
                                        expected_native_bbox=SMALL_LAYER_NATIVE_BBOX,
                                        expected_native_crs=native_crs)

    expected_bbox = (1571000.0, 6268800.0, 1572590.854206196, 6269876.33561699)
    exp_native_bbox = (14.112533113517683, 48.964264493114904, 14.126824, 48.970612)
    method_bbox_thumbnail_tuples = [
        (data_wfs.get_wfs20_insert_points, expected_bbox, exp_native_bbox, '_bigger'),
        (data_wfs.get_wfs20_delete_point, SMALL_LAYER_BBOX, SMALL_LAYER_NATIVE_BBOX, ''),
    ]

    for wfs_method, exp_bbox, exp_native_bbox, thumbnail_bbox_postfix in method_bbox_thumbnail_tuples:
        data_xml = wfs_method(workspace, layer, )

        process_client.post_wfst(data_xml, workspace=workspace)
        process_client.wait_for_publication_status(workspace, process_client.LAYER_TYPE, layer)

        assert_util.assert_all_sources_bbox(workspace, layer, exp_bbox, expected_native_bbox=exp_native_bbox,
                                            expected_native_crs=native_crs)

        expected_thumbnail_path = f'/code/sample/style/{layer}{thumbnail_style_postfix}{thumbnail_bbox_postfix}.png'
        with app.app_context():
            thumbnail_path = thumbnail.get_layer_thumbnail_path(workspace, layer)
        diffs = test_util.compare_images(expected_thumbnail_path, thumbnail_path)
        assert diffs < 100, expected_thumbnail_path

    process_client.delete_workspace_layer(workspace, layer, )
