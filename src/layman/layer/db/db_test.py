import os
import shutil
import time
import sys
import uuid

import pytest
from db import TableUri

del sys.modules['layman']

from layman import app as layman, settings
from layman.layer.filesystem.input_file import ensure_layer_input_file_dir
from layman.layer.filesystem.util import get_layer_dir
from layman.layer.layer_class import Layer
from layman.common import bbox as bbox_util
from layman.common.prime_db_schema import publications
from layman.layer import db
from test_tools import prime_db_schema_client
from test_tools.process_client import LAYER_TYPE
from . import table as table_util


WORKSPACE = 'db_testuser'


def post_layer(workspace, layername, file_path):
    publ_uuid = str(uuid.uuid4())
    with layman.app_context():
        db.ensure_workspace(workspace)
        prime_db_schema_client.post_workspace_publication(LAYER_TYPE, workspace, layername,
                                                          geodata_type=settings.GEODATA_TYPE_VECTOR,
                                                          wfs_wms_status=settings.EnumWfsWmsStatus.AVAILABLE.value,
                                                          publ_uuid=publ_uuid,
                                                          )
        ensure_layer_input_file_dir(publ_uuid)
        layer = Layer(uuid=publ_uuid)
        db.import_vector_file_to_internal_table(layer.table_uri.schema, layer.table_uri.table, file_path, None)

    yield layer.table_uri

    with layman.app_context():
        table_util.delete_layer_by_class(layer=layer)
        publications.delete_publication(workspace, LAYER_TYPE, layername)


@pytest.fixture(scope="function")
def posted_layer(request):
    layer_name, file_path = request.param
    yield from post_layer(WORKSPACE, layer_name, file_path)


@pytest.fixture(scope="module")
def boundary_table():
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp'
    workspace = WORKSPACE
    layername = 'hranice'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def road_table():
    file_path = 'sample/data/upper_attr.geojson'
    workspace = WORKSPACE
    layername = 'silnice'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def country_table():
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp'
    workspace = WORKSPACE
    layername = 'staty'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def country110m_table():
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'
    workspace = WORKSPACE
    layername = 'staty110m'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def country50m_table():
    file_path = 'tmp/naturalearth/50m/cultural/ne_50m_admin_0_countries.geojson'
    workspace = WORKSPACE
    layername = 'staty50m'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def country10m_table():
    file_path = 'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson'
    workspace = WORKSPACE
    layername = 'staty10m'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def data200road_table():
    file_path = 'tmp/data200/trans/RoadL.shp'
    workspace = WORKSPACE
    layername = 'data200_road'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def sm5building_table():
    file_path = 'tmp/sm5/vektor/Budova.shp'
    workspace = WORKSPACE
    layername = 'sm5_building'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def populated_places_table():
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson'
    workspace = WORKSPACE
    layername = 'ne_110m_populated_places'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def empty_table():
    file_path = 'sample/layman.layer/empty.shp'
    workspace = WORKSPACE
    layername = 'empty'
    yield from post_layer(workspace, layername, file_path)


@pytest.fixture(scope="module")
def single_point_table():
    file_path = 'sample/layman.layer/single_point.shp'
    workspace = WORKSPACE
    layername = 'single_point'
    yield from post_layer(workspace, layername, file_path)


def test_abort_import_layer_vector_file():
    workspace = 'testuser1'
    layername = 'ne_10m_admin_0_countries'
    src_dir = 'tmp/naturalearth/10m/cultural'
    publ_uuid = '685c32c9-e4f6-4bdc-b220-042b3e3b971e'
    with layman.app_context():
        input_file_dir = ensure_layer_input_file_dir(publ_uuid)
    filename = layername + '.geojson'
    main_filepath = os.path.join(input_file_dir, filename)

    crs_id = None
    shutil.copy(
        os.path.join(src_dir, filename),
        input_file_dir
    )

    def abort_layer_import():
        prime_db_schema_client.post_workspace_publication(LAYER_TYPE, workspace, layername,
                                                          geodata_type=settings.GEODATA_TYPE_VECTOR,
                                                          wfs_wms_status=settings.EnumWfsWmsStatus.AVAILABLE.value,
                                                          publ_uuid=publ_uuid,
                                                          )
        with layman.app_context():
            layer = Layer(uuid=publ_uuid)
        table_uri = layer.table_uri
        process = db.import_vector_file_to_internal_table_async(table_uri.schema, table_uri.table, main_filepath,
                                                                crs_id)
        time1 = time.time()
        while process.poll() is None:
            if time.time() - time1 > 0.1:
                # print('terminating process')
                process.terminate()
            time.sleep(0.1)

        return_code = process.poll()
        return return_code

    return_code = abort_layer_import()
    assert return_code != 0
    with layman.app_context():
        publications.delete_publication(workspace, LAYER_TYPE, layername)
        layerdir = get_layer_dir(publ_uuid)
    shutil.rmtree(layerdir)


def test_data_language(boundary_table: TableUri):
    with layman.app_context():
        col_names = db.get_text_column_names(boundary_table.schema, boundary_table.table)
    assert set(col_names) == set(['featurecla', 'name', 'name_alt'])
    with layman.app_context():
        text_data, _ = db.get_text_data(boundary_table.schema, boundary_table.table, boundary_table.primary_key_column)
    # print(f"num_rows={num_rows}")
    assert len(text_data) == 1
    assert text_data[0].startswith(' '.join(['International boundary (verify)'] * 100))
    with layman.app_context():
        langs = db.get_text_languages(boundary_table.schema, boundary_table.table, boundary_table.primary_key_column)
    assert langs == ['eng']


def test_data_language_roads(road_table: TableUri):
    with layman.app_context():
        col_names = db.get_text_column_names(road_table.schema, road_table.table)
    assert set(col_names) == set([
        'cislouseku',
        'dpr_smer_p',
        'etah1',
        'etah2',
        'etah3',
        'etah4',
        'fid_zbg',
        'jmeno',
        'kruh_obj_k',
        'kruh_obj_p',
        'peazkom1',
        'peazkom2',
        'peazkom3',
        'peazkom4',
        'r_indsil7',
        'silnice',
        'silnice_bs',
        'typsil_k',
        'typsil_p',
        'vym_tahy_k',
        'vym_tahy_p'
    ])
    with layman.app_context():
        langs = db.get_text_languages(road_table.schema, road_table.table, road_table.primary_key_column)
    assert langs == ['cze']


def test_populated_places_table(populated_places_table: TableUri):
    with layman.app_context():
        col_names = db.get_text_column_names(populated_places_table.schema, populated_places_table.table)
    assert len(col_names) == 31
    with layman.app_context():
        langs = db.get_text_languages(populated_places_table.schema, populated_places_table.table,
                                      populated_places_table.primary_key_column)
    assert set(langs) == set(['chi', 'eng', 'rus'])


def test_data_language_countries(country_table: TableUri):
    with layman.app_context():
        col_names = db.get_text_column_names(country_table.schema, country_table.table)
    assert len(col_names) == 63
    with layman.app_context():
        langs = db.get_text_languages(country_table.schema, country_table.table, country_table.primary_key_column)
    assert set(langs) == set([
        'ara',
        'ben',
        'chi',
        'eng',
        'fre',
        'gre',
        'hin',
        'hun',
        'jpn',
        'kor',
        'pol',
        'por',
        'rus',
        'tur',
        'vie',
    ])


def test_data_language_countries2(country110m_table: TableUri):
    # col_names = db.get_text_column_names(country110m_table.schema, country110m_table.table)
    # print(col_names)
    # assert len(col_names) == 63
    with layman.app_context():
        langs = db.get_text_languages(country110m_table.schema, country110m_table.table,
                                      country110m_table.primary_key_column)
    assert set(langs) == set(['eng'])


def guess_scale_denominator(table_uri: TableUri):
    return db.guess_scale_denominator(table_uri.schema, table_uri.table, table_uri.primary_key_column,
                                      table_uri.geo_column)


def test_guess_scale_denominator(country110m_table: TableUri, country50m_table: TableUri, country10m_table: TableUri,
                                 data200road_table: TableUri, sm5building_table: TableUri):
    with layman.app_context():
        sd_110m = guess_scale_denominator(country110m_table)
    assert 25000000 <= sd_110m <= 500000000
    assert sd_110m == 100000000
    with layman.app_context():
        sd_50m = guess_scale_denominator(country50m_table)
    assert 10000000 <= sd_50m <= 250000000
    assert sd_50m == 10000000
    with layman.app_context():
        sd_10m = guess_scale_denominator(country10m_table)
    assert 2500000 <= sd_10m <= 50000000
    assert sd_10m == 2500000
    with layman.app_context():
        sd_200k = guess_scale_denominator(data200road_table)
    assert 50000 <= sd_200k <= 1000000
    assert sd_200k == 100000
    with layman.app_context():
        sd_5k = guess_scale_denominator(sm5building_table)
    assert 1000 <= sd_5k <= 25000
    assert sd_5k == 5000


@pytest.mark.parametrize("posted_layer, exp_result", [
    pytest.param(('25k_vertexes', 'sample/layman.layer/25k_vertexes.geojson'), 5000, id='25k_vertexes',
                 marks=pytest.mark.timeout(5, method="thread"))
], indirect=["posted_layer"])
def test_guess_scale_denominator_performance(posted_layer: TableUri, exp_result):
    with layman.app_context():
        result = guess_scale_denominator(posted_layer)
    assert result == exp_result


def test_empty_table_bbox(empty_table: TableUri):
    with layman.app_context():
        bbox = db.get_bbox(empty_table.schema, empty_table.table, column=empty_table.geo_column)
    assert bbox_util.is_empty(bbox), bbox


def test_single_point_table_bbox(single_point_table: TableUri):
    with layman.app_context():
        bbox = db.get_bbox(single_point_table.schema, single_point_table.table, column=single_point_table.geo_column)
    assert bbox[0] == bbox[2] and bbox[1] == bbox[3], bbox
