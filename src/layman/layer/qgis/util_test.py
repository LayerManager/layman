import pytest

from layman import app, LaymanError
from test_tools import process_client, util as test_util
from . import util
from .. import db
from ..filesystem import thumbnail


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
    ('none_geometry', set(), {
        'Point': ('Point', None),
        'Line': ('MultiLineString', None),
        'Polygon': ('MultiPolygon', None),
    }),
])
@pytest.mark.usefixtures('ensure_layman')
def test_geometry_types(layer, exp_db_types, qml_geometry_dict):
    def get_qml_style_path(style_name):
        return f'/code/sample/data/geometry-types/{style_name}.qml' if style_name else None

    workspace = 'test_geometry_types_workspace'
    process_client.publish_workspace_layer(workspace, layer, file_paths=[f'/code/sample/data/geometry-types/{layer}.geojson'], )
    with app.app_context():
        table_name = db.get_internal_table_name(workspace, layer)
        db_types = db.get_geometry_types(workspace, table_name)
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
