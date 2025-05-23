import pytest

import crs as crs_def
from layman import app
from layman.common.prime_db_schema import publications
from test_tools import process_client, assert_util, data as test_data
from test_tools.mock.layman_classes import LayerMock
from . import wfs, wms, tasks


@pytest.mark.usefixtures('ensure_layman')
def test_geoserver_bbox():
    workspace = 'test_geoserver_bbox_workspace'
    layer = 'test_geoserver_bbox_layer'
    expected_bbox_1 = test_data.SMALL_LAYER_BBOX
    crs = crs_def.EPSG_3857
    no_area_bbox_padding = crs_def.CRSDefinitions[crs].no_area_bbox_padding
    expected_bboxes = [((1571203, 6268895, 1572589, 6269864), (1571203, 6268895, 1572589, 6269864)),
                       ((1571203, 6268895, 1571203, 6269864), (1571203 - no_area_bbox_padding, 6268895,
                                                               1571203 + no_area_bbox_padding, 6269864)),  # line
                       ((1571203, 6268895, 1571203, 6268895), (1571203 - no_area_bbox_padding,
                                                               6268895 - no_area_bbox_padding,
                                                               1571203 + no_area_bbox_padding,
                                                               6268895 + no_area_bbox_padding)),  # point
                       ((None, None, None, None), crs_def.CRSDefinitions[crs].max_bbox),
                       ]

    response = process_client.publish_workspace_layer(workspace, layer, style_file='sample/style/small_layer.qml')
    uuid = response['uuid']
    layer_class = LayerMock(uuid=uuid, layer_tuple=(workspace, layer))

    assert_util.assert_wfs_bbox(uuid, expected_bbox_1)
    assert_util.assert_wms_bbox(uuid, expected_bbox_1)

    kwargs = {
        'access_rights': None,
        'uuid': response['uuid'],
    }
    wms_kwargs = {
        **kwargs,
        'store_in_geoserver': True,
    }

    # test WFS
    for bbox, expected_bbox in expected_bboxes:
        with app.app_context():
            wfs.delete_layer(layer_class)
            publications.set_bbox(workspace, process_client.LAYER_TYPE, layer, bbox, crs, )
            wfs.delete_layer(layer_class)
            tasks.refresh_wfs.apply(args=[workspace, layer],
                                    kwargs=kwargs,
                                    )
        assert_util.assert_wfs_bbox(uuid, expected_bbox)

    # test WMS
    for bbox, expected_bbox in expected_bboxes:
        with app.app_context():
            wms.delete_layer(layer_class)
            publications.set_bbox(workspace, process_client.LAYER_TYPE, layer, bbox, crs, )
            tasks.refresh_wms.apply(args=[workspace, layer],
                                    kwargs=wms_kwargs,
                                    )
        assert_util.assert_wms_bbox(uuid, expected_bbox)

    # test cascade WMS from QGIS
    for bbox, expected_bbox in expected_bboxes:
        with app.app_context():
            wms.delete_layer(layer_class)
            publications.set_bbox(workspace, process_client.LAYER_TYPE, layer, bbox, crs, )
            wms.delete_layer(layer_class)
            tasks.refresh_wms.apply(args=[workspace, layer],
                                    kwargs=wms_kwargs,
                                    )
        assert_util.assert_wms_bbox(uuid, expected_bbox)

    process_client.delete_workspace_layer(workspace, layer)
