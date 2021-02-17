import os
from lxml import etree as ET
import pytest
import requests
from . import util, wms as qgis_wms
from layman import app, settings, LaymanError
from .. import db
from test import process_client
from owslib.wms import WebMapService


@pytest.mark.usefixtures('ensure_layman')
def test_fill_project_template():
    workspace = 'test_fill_project_template_workspace'
    layer = 'test_fill_project_template_layer'
    qgs_path = f'{settings.LAYMAN_QGIS_DATA_DIR}/{layer}.qgs'
    wms_url = f'{settings.LAYMAN_QGIS_URL}?MAP={qgs_path}'

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
    qml_path = '/code/sample/style/funny_qml.xml'
    parser = ET.XMLParser(remove_blank_text=True)
    qml_xml = ET.parse(qml_path, parser=parser)
    with app.app_context():
        db_types = db.get_geometry_types(workspace, layer)
    qml_geometry = util.get_qml_geometry_from_qml(qml_xml)
    source_type = util.get_source_type(db_types, qml_geometry)
    layer_qml = util.fill_layer_template(workspace, layer, layer_uuid, layer_bbox, qml_xml, source_type)
    qgs_str = util.fill_project_template(workspace, layer, layer_uuid, layer_qml, settings.LAYMAN_OUTPUT_SRS_LIST, layer_bbox, source_type)
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


@pytest.mark.parametrize('layer, exp_db_types, qml_geometry_to_exp_source_type', [
    ('all', {'ST_Point', 'ST_MultiPoint', 'ST_LineString', 'ST_MultiLineString', 'ST_Polygon', 'ST_MultiPolygon', 'ST_GeometryCollection'}, {
        'Point': 'MultiPoint',
        'Line': 'MultiCurve',
        'Polygon': 'MultiSurface',
        'Unknown geometry': 'GeometryCollection',
    }),
    ('geometrycollection', {'ST_GeometryCollection'}, {
        'Unknown geometry': 'GeometryCollection',
    }),
    ('linestring', {'ST_LineString'}, {
        'Line': 'LineString',
    }),
    ('multilinestring', {'ST_MultiLineString'}, {
        'Line': 'MultiLineString',
    }),
    ('multipoint', {'ST_MultiPoint'}, {
        'Point': 'MultiPoint',
    }),
    ('multipolygon', {'ST_MultiPolygon'}, {
        'Polygon': 'MultiPolygon',
    }),
    ('point', {'ST_Point'}, {
        'Point': 'Point',
    }),
    ('polygon', {'ST_Polygon'}, {
        'Polygon': 'Polygon',
    }),
])
@pytest.mark.usefixtures('ensure_layman')
def test_geometry_types(layer, exp_db_types, qml_geometry_to_exp_source_type):
    workspace = 'test_geometry_types_workspace'
    process_client.publish_layer(workspace, layer, file_paths=[f'/code/sample/data/geometry-types/{layer}.geojson'],)
    with app.app_context():
        db_types = db.get_geometry_types(workspace, layer)
    assert set(db_types) == exp_db_types

    qgis_geometries = ['Point', 'Line', 'Polygon', 'Unknown geometry']

    for qml_geometry in qgis_geometries:
        exp_source_type = qml_geometry_to_exp_source_type.get(qml_geometry)
        if exp_source_type is None:
            with pytest.raises(LaymanError) as excinfo:
                source_type = util.get_source_type(db_types, qml_geometry)
            assert excinfo.value.code == 47, f"qml_geometry={qml_geometry}, exp_source_type={exp_source_type}"
        else:
            source_type = util.get_source_type(db_types, qml_geometry)
            assert source_type == exp_source_type, f"qml_geometry={qml_geometry}, exp_source_type={exp_source_type}, source_type={source_type}, db_types={db_types}"

    process_client.delete_layer(workspace, layer)
