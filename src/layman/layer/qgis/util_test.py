import os
from test import process_client, util as test_util
from lxml import etree as ET
import requests
from owslib.wms import WebMapService
import pytest
from layman import app, settings, LaymanError
from layman.common import bbox as bbox_util
from . import util
from .. import db
from ..filesystem import thumbnail


@pytest.mark.usefixtures('ensure_layman')
def test_fill_project_template():
    workspace = 'test_fill_project_template_workspace'
    layer = 'test_fill_project_template_layer'
    qgs_path = f'{settings.LAYMAN_QGIS_DATA_DIR}/{layer}.qgs'
    wms_url = f'{settings.LAYMAN_QGIS_URL}?MAP={qgs_path}'
    wms_version = '1.3.0'

    layer_info = process_client.publish_workspace_layer(workspace,
                                                        layer,
                                                        file_paths=['/code/tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson'],
                                                        )

    layer_uuid = layer_info['uuid']

    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        WebMapService(wms_url, version=wms_version)
    assert excinfo.value.response.status_code == 500

    with app.app_context():
        layer_bbox = db.get_bbox(workspace, layer)
    layer_bbox = layer_bbox if not bbox_util.is_empty(layer_bbox) else settings.LAYMAN_DEFAULT_OUTPUT_BBOX
    qml_path = '/code/sample/style/ne_10m_admin_0_countries.qml'
    parser = ET.XMLParser(remove_blank_text=True)
    qml_xml = ET.parse(qml_path, parser=parser)
    exp_min_scale = '200000000'
    template_xml = ET.parse(util.get_layer_template_path(), parser=parser)
    assert qml_xml.getroot().attrib['minScale'] == exp_min_scale
    assert template_xml.getroot().attrib['minScale'] != exp_min_scale
    with app.app_context():
        db_types = db.get_geometry_types(workspace, layer)
        db_cols = [
            col for col in db.get_all_column_infos(workspace, layer)
            if col.name not in ['wkb_geometry', 'ogc_fid']
        ]
    qml_geometry = util.get_qml_geometry_from_qml(qml_xml)
    source_type = util.get_source_type(db_types, qml_geometry)
    layer_qml_str = util.fill_layer_template(workspace, layer, layer_uuid, layer_bbox, qml_xml, source_type, db_cols)
    layer_qml = ET.fromstring(layer_qml_str.encode('utf-8'), parser=parser)
    assert layer_qml.attrib['minScale'] == exp_min_scale
    qgs_str = util.fill_project_template(workspace, layer, layer_uuid, layer_qml_str, settings.LAYMAN_OUTPUT_SRS_LIST, layer_bbox,
                                         source_type)
    with open(qgs_path, "w") as qgs_file:
        print(qgs_str, file=qgs_file)

    wmsi = WebMapService(wms_url, version=wms_version)
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
        WebMapService(wms_url, version=wms_version)
    assert excinfo.value.response.status_code == 500

    process_client.delete_workspace_layer(workspace, layer)


@pytest.mark.parametrize('layer, exp_db_types, qml_geometry_dict', [
    ('all', {'ST_Point', 'ST_MultiPoint', 'ST_LineString', 'ST_MultiLineString', 'ST_Polygon', 'ST_MultiPolygon',
             'ST_GeometryCollection'}, {
        'Point': ('MultiPoint', 'point'),
        'Line': ('MultiCurve', 'line'),
        'Polygon': ('MultiSurface', 'polygon'),
        'Unknown geometry': ('GeometryCollection', None),
    }),
    ('geometrycollection', {'ST_GeometryCollection'}, {
        'Unknown geometry': ('GeometryCollection', None),
    }),
    ('linestring', {'ST_LineString'}, {
        'Line': ('LineString', 'line'),
    }),
    ('multilinestring', {'ST_MultiLineString'}, {
        'Line': ('MultiLineString', None),
    }),
    ('multipoint', {'ST_MultiPoint'}, {
        'Point': ('MultiPoint', None),
    }),
    ('multipolygon', {'ST_MultiPolygon'}, {
        'Polygon': ('MultiPolygon', None),
    }),
    ('point', {'ST_Point'}, {
        'Point': ('Point', 'point'),
    }),
    ('polygon', {'ST_Polygon'}, {
        'Polygon': ('Polygon', 'polygon'),
    }),
])
@pytest.mark.usefixtures('ensure_layman')
def test_geometry_types(layer, exp_db_types, qml_geometry_dict):
    def get_qml_style_path(style_name):
        return f'/code/sample/data/geometry-types/{style_name}.qml' if style_name else None

    workspace = 'test_geometry_types_workspace'
    process_client.publish_workspace_layer(workspace, layer, file_paths=[f'/code/sample/data/geometry-types/{layer}.geojson'], )
    with app.app_context():
        db_types = db.get_geometry_types(workspace, layer)
    assert set(db_types) == exp_db_types

    qgis_geometries = ['Point', 'Line', 'Polygon', 'Unknown geometry']

    old_qml_style_name = None
    for qml_geometry in qgis_geometries:
        exp_source_type, new_qml_style_name = qml_geometry_dict.get(qml_geometry, (None, None))
        if exp_source_type is None:
            with pytest.raises(LaymanError) as excinfo:
                util.get_source_type(db_types, qml_geometry)
            assert excinfo.value.code == 47, f"qml_geometry={qml_geometry}, exp_source_type={exp_source_type}"
        else:
            source_type = util.get_source_type(db_types, qml_geometry)
            assert source_type == exp_source_type, f"qml_geometry={qml_geometry}, exp_source_type={exp_source_type}, " \
                                                   f"source_type={source_type}, db_types={db_types}"
        if new_qml_style_name:
            if new_qml_style_name != old_qml_style_name:
                process_client.patch_workspace_layer(workspace, layer, style_file=get_qml_style_path(new_qml_style_name))
                old_qml_style_name = new_qml_style_name
            with app.app_context():
                qml = util.get_original_style_xml(workspace, layer)
            found_qml_geometry = util.get_qml_geometry_from_qml(qml)
            assert found_qml_geometry == qml_geometry
            exp_file_path = f'/code/sample/data/geometry-types/{new_qml_style_name}.png'
            with app.app_context():
                thumbnail_path = thumbnail.get_layer_thumbnail_path(workspace, layer)
            diff_pixels = test_util.compare_images(thumbnail_path, exp_file_path)
            assert diff_pixels == 0, f"thumbnail_path={thumbnail_path}, exp_file_path={exp_file_path}"

    process_client.delete_workspace_layer(workspace, layer)
