import os
import pytest
import requests
from . import util, wms as qgis_wms
from layman import app, settings
from .. import db
from test import process_client
from owslib.wms import WebMapService


@pytest.mark.usefixtures('ensure_layman')
def test_fill_project_template():
    workspace = 'test_fill_project_template_workspace'
    layer = 'test_fill_project_template_layer'
    qgs_path = f'{settings.LAYMAN_QGIS_DATA_DIR}/{layer}.qgs'
    wms_url = f"{settings.LAYMAN_QGIS_URL}?MAP={qgs_path}"

    layer_info = process_client.publish_layer(workspace,
                                              layer,
                                              file_paths=['/code/tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson'],
                                              )

    layer_uuid = layer_info['uuid']

    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        WebMapService(wms_url, version=qgis_wms.VERSION)
    assert excinfo.value.response.status_code == 500

    with app.app_context():
        layer_bbox = db.get_bbox(workspace, layer)
    layer_bbox = layer_bbox or settings.LAYMAN_DEFAULT_OUTPUT_BBOX
    layer_qml = util.fill_layer_template(workspace, layer, layer_uuid, layer_bbox)
    qgs_str = util.fill_project_template(workspace, layer, layer_uuid, layer_qml, settings.LAYMAN_OUTPUT_SRS_LIST, layer_bbox)
    with open(qgs_path, "w") as qgs_file:
        print(qgs_str, file=qgs_file)

    wmsi = WebMapService(wms_url, version=qgis_wms.VERSION)
    assert layer in wmsi.contents
    wms_layer = wmsi.contents[layer]
    for expected_output_srs in settings.LAYMAN_OUTPUT_SRS_LIST:
        assert f"EPSG:{expected_output_srs}" in wms_layer.crsOptions
    wms_layer_bbox = next((tuple(bbox_crs[:4]) for bbox_crs in wms_layer.crs_list if bbox_crs[4] == f"EPSG:3857"))
    precision = 0.1
    for idx, expected_coordinate in enumerate(layer_bbox):
        assert abs(expected_coordinate - wms_layer_bbox[idx]) <= precision

    os.remove(qgs_path)

    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        WebMapService(wms_url, version=qgis_wms.VERSION)
    assert excinfo.value.response.status_code == 500

    process_client.delete_layer(workspace, layer)
