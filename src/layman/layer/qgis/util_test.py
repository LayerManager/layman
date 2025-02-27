from lxml import etree as ET
import pytest

from layman import app, LaymanError
from layman.layer.layer_class import Layer
from test_tools import process_client, util as test_util
from . import util
from .. import db
from ..filesystem import thumbnail


@pytest.mark.parametrize('qml_version', ['3.16.2', '3.40.2'])
@pytest.mark.parametrize('layername, exp_db_types, qml_geometry_dict', [
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
    ('none_geometry', set(), {
        'Point': ('Point', None),
        'Line': ('MultiLineString', None),
        'Polygon': ('MultiPolygon', None),
    }),
])
@pytest.mark.usefixtures('ensure_layman')
def test_geometry_types(layername, exp_db_types, qml_geometry_dict, qml_version):
    workspace = 'test_geometry_types_workspace'
    process_client.publish_workspace_layer(
        workspace, layername, file_paths=[f'/code/sample/data/geometry-types/{layername}.geojson']
    )
    with app.app_context():
        layer = Layer(layer_tuple=(workspace, layername))
        table_uri = layer.table_uri
        db_types = db.get_geometry_types(table_uri.schema, table_uri.table)
    assert set(db_types) == exp_db_types

    qgis_geometries = ['Point', 'Line', 'Polygon', 'Unknown geometry']

    for qml_geometry in qgis_geometries:
        exp_source_type, qml_style_name = qml_geometry_dict.get(qml_geometry, (None, None))
        if exp_source_type is None:
            with pytest.raises(LaymanError) as excinfo:
                util.get_source_type(db_types, qml_geometry)
            assert excinfo.value.code == 47, f"qml_geometry={qml_geometry}, exp_source_type={exp_source_type}"
        else:
            source_type = util.get_source_type(db_types, qml_geometry)
            assert source_type == exp_source_type, f"qml_geometry={qml_geometry}, exp_source_type={exp_source_type}, " \
                                                   f"source_type={source_type}, db_types={db_types}"
        if qml_style_name:
            style_file_path = f'/code/sample/data/geometry-types/{qml_style_name}-v{qml_version}.qml'
            process_client.patch_workspace_layer(layer.workspace, layer.name, style_file=style_file_path)
            with app.app_context():
                qml = util.get_original_style_xml(layer.uuid)
            found_qml_geometry = util.get_geometry_from_qml_and_db_types(qml, db_types=[])
            assert found_qml_geometry == qml_geometry
            exp_file_path = f'/code/sample/data/geometry-types/{qml_style_name}.png'
            diff_pixels_limit = {
                'line': 250,
                'point': 10,
                'polygon': 110,
            }[qml_style_name]
            with app.app_context():
                thumbnail_path = thumbnail.get_layer_thumbnail_path(layer.uuid)
            diff_pixels = test_util.compare_images(thumbnail_path, exp_file_path)
            assert diff_pixels < diff_pixels_limit, f"thumbnail_path={thumbnail_path}, exp_file_path={exp_file_path}"

    process_client.delete_workspace_layer(layer.workspace, layer.name)


@pytest.mark.parametrize('qml_path, exp_qml_type', [
    ('sample/style/small_layer.qml', 'Polygon'),
    ('sample/style/labels_without_symbols/KATASTRALNI_UZEMI_P.qml', 'Polygon'),
    ('sample/style/labels_without_symbols/KATASTRALNI_UZEMI_L.qml', 'Line'),
    ('sample/style/labels_without_symbols/BODOVE_POLE_T.qml', 'Unknown'),
    ('sample/style/labels_without_symbols/DALSI_PRVKY_MAPY_T.qml', 'Unknown'),
    ('sample/style/labels_without_symbols/KATASTRALNI_UZEMI_DEF.qml', 'Unknown'),
    ('sample/style/labels_without_symbols/PRVKY_ORIENT_MAPY_T.qml', 'Unknown'),
    ('sample/style/cluster.qml', 'Point'),
])
def test__get_qml_geometry_from_qml(qml_path, exp_qml_type):
    parser = ET.XMLParser(remove_blank_text=True)
    qml_xml = ET.parse(qml_path, parser=parser)
    # pylint: disable=protected-access
    result = util._get_qml_geometry_from_qml(qml_xml)
    assert result == exp_qml_type


@pytest.mark.parametrize('qml_path, db_types, exp_qml_type', [
    ('sample/style/small_layer.qml', [], 'Polygon'),
    ('sample/style/labels_without_symbols/KATASTRALNI_UZEMI_P.qml', [], 'Polygon'),
    ('sample/style/labels_without_symbols/KATASTRALNI_UZEMI_L.qml', [], 'Line'),
    ('sample/style/labels_without_symbols/BODOVE_POLE_T.qml', ["ST_Point"], 'Point'),
    ('sample/style/labels_without_symbols/BODOVE_POLE_T.qml', [], 'Point'),
])
def test_get_qml_geometry_from_qml(qml_path, db_types, exp_qml_type):
    parser = ET.XMLParser(remove_blank_text=True)
    qml_xml = ET.parse(qml_path, parser=parser)
    result = util.get_geometry_from_qml_and_db_types(qml_xml, db_types)
    assert result == exp_qml_type


@pytest.mark.parametrize('qml_path, db_types, exp_message', [
    pytest.param(
        'sample/style/labels_without_symbols/BODOVE_POLE_T.qml',
        ["ST_Polygon"],
        'Unknown QGIS geometry type "Unknown". Geometries in DB: [\'ST_Polygon\'].',
        id='point_qml_with_polygon',
    ),
])
def test_get_qml_geometry_from_qml_raises(qml_path, db_types, exp_message):
    parser = ET.XMLParser(remove_blank_text=True)
    qml_xml = ET.parse(qml_path, parser=parser)
    with pytest.raises(LaymanError) as exc_info:
        util.get_geometry_from_qml_and_db_types(qml_xml, db_types)
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 47
    assert exc_info.value.message == 'Error in QML'
    assert exc_info.value.data == exp_message
