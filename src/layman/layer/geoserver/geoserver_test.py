from test import process_client, util as test_util, data as test_data
import pytest

from layman import app, settings
from layman.common import bbox as bbox_util
from layman.common.prime_db_schema import publications
from layman.http import LaymanError
from . import wfs, wms, tasks


@pytest.mark.usefixtures('ensure_layman')
def test_check_workspace_wms():
    workspace = 'test_check_workspace_wms_user' + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX
    layer = 'test_check_workspace_wms_layer'
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_layer(workspace, layer)
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 45
    assert exc_info.value.data['workspace_name'] == workspace


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_check_user_wms():
    user = 'test_check_user_wms' + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX
    auth_headers = process_client.get_authz_headers(user)
    with pytest.raises(LaymanError) as exc_info:
        process_client.reserve_username(user, headers=auth_headers)
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 45
    assert exc_info.value.data['workspace_name'] == user


def assert_wfs_bbox(workspace, layer, expected_bbox):
    wfs_layer = f"{workspace}:{layer}"
    wfs_get_capabilities = wfs.get_wfs_proxy(workspace)
    wfs_bbox_4326 = wfs_get_capabilities.contents[wfs_layer].boundingBoxWGS84
    wfs_bbox_3857 = bbox_util.transform(wfs_bbox_4326, 4326, 3857, )
    test_util.assert_same_bboxes(expected_bbox, wfs_bbox_3857, 0.00001)


def assert_wms_bbox(workspace, layer, expected_bbox):
    wms_get_capabilities = wms.get_wms_proxy(workspace)
    wms_bboxes = wms_get_capabilities.contents[layer].crs_list
    wms_bbox_3857 = next(bbox[:4] for bbox in wms_bboxes if bbox[4] == 'EPSG:3857')
    test_util.assert_same_bboxes(expected_bbox, wms_bbox_3857, 0.00001)


@pytest.mark.usefixtures('ensure_layman')
def test_geoserver_bbox():
    workspace = 'test_geoserver_bbox_workspace'
    layer = 'test_geoserver_bbox_layer'
    expected_bbox_1 = test_data.SMALL_LAYER_BBOX
    expected_bboxes = [((1571203, 6268895, 1572589, 6269864), (1571203, 6268895, 1572589, 6269864)),
                       ((1571203, 6268895, 1571203, 6269864), (1571203 - settings.NO_AREA_BBOX_PADDING, 6268895,
                                                               1571203 + settings.NO_AREA_BBOX_PADDING, 6269864)),  # line
                       ((1571203, 6268895, 1571203, 6268895), (1571203 - settings.NO_AREA_BBOX_PADDING,
                                                               6268895 - settings.NO_AREA_BBOX_PADDING,
                                                               1571203 + settings.NO_AREA_BBOX_PADDING,
                                                               6268895 + settings.NO_AREA_BBOX_PADDING)),  # point
                       ((None, None, None, None), settings.LAYMAN_DEFAULT_OUTPUT_BBOX),
                       ]

    process_client.publish_workspace_layer(workspace, layer, style_file='sample/style/small_layer.qml')

    with app.app_context():
        assert_wfs_bbox(workspace, layer, expected_bbox_1)
        assert_wms_bbox(workspace, layer, expected_bbox_1)

        # test WFS
        for bbox, expected_bbox in expected_bboxes:
            publications.set_bbox(workspace, process_client.LAYER_TYPE, layer, bbox)
            wfs.delete_layer(workspace, layer)
            tasks.refresh_wfs.apply(args=[workspace, layer],
                                    description=layer,
                                    title=layer,
                                    ensure_user=False,
                                    access_rights=None,
                                    )
            assert_wfs_bbox(workspace, layer, expected_bbox)

        # test WMS
        for bbox, expected_bbox in expected_bboxes:
            publications.set_bbox(workspace, process_client.LAYER_TYPE, layer, bbox)
            wms.delete_layer(workspace, layer)
            tasks.refresh_wms.apply(args=[workspace, layer, True],
                                    description=layer,
                                    title=layer,
                                    ensure_user=False,
                                    access_rights=None,
                                    )
            assert_wms_bbox(workspace, layer, expected_bbox)

        # test cascade WMS from QGIS
        for bbox, expected_bbox in expected_bboxes:
            publications.set_bbox(workspace, process_client.LAYER_TYPE, layer, bbox)
            wms.delete_layer(workspace, layer)
            tasks.refresh_wms.apply(args=[workspace, layer, False],
                                    description=layer,
                                    title=layer,
                                    ensure_user=False,
                                    access_rights=None,
                                    )
            assert_wms_bbox(workspace, layer, expected_bbox)

    process_client.delete_workspace_layer(workspace, layer)
