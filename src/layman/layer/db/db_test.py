import os
import shutil
import time
import sys
import pytest

del sys.modules['layman']

from layman import app as layman
from layman.layer.filesystem.input_file import ensure_layer_input_file_dir
from layman.layer.filesystem.util import get_layer_dir
from layman.common import bbox as bbox_util
from layman.layer import db
from . import table as table_util


WORKSPACE = 'db_testuser'


def post_layer(workspace, layer, file_path):
    with layman.app_context():
        db.ensure_workspace(workspace)
        ensure_layer_input_file_dir(workspace, layer)
        db.import_layer_vector_file(workspace, layer, file_path, None)


def delete_layer(workspace, layer,):
    with layman.app_context():
        table_util.delete_layer(workspace, layer)


@pytest.fixture()
def boundary_table():
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp'
    workspace = WORKSPACE
    layername = 'hranice'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def road_table():
    file_path = 'sample/data/upper_attr.geojson'
    workspace = WORKSPACE
    layername = 'silnice'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def country_table():
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp'
    workspace = WORKSPACE
    layername = 'staty'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def country110m_table():
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'
    workspace = WORKSPACE
    layername = 'staty110m'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def country50m_table():
    file_path = 'tmp/naturalearth/50m/cultural/ne_50m_admin_0_countries.geojson'
    workspace = WORKSPACE
    layername = 'staty50m'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def country10m_table():
    file_path = 'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson'
    workspace = WORKSPACE
    layername = 'staty10m'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def data200road_table():
    file_path = 'tmp/data200/trans/RoadL.shp'
    workspace = WORKSPACE
    layername = 'data200_road'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def sm5building_table():
    file_path = 'tmp/sm5/vektor/Budova.shp'
    workspace = WORKSPACE
    layername = 'sm5_building'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def populated_places_table():
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson'
    workspace = WORKSPACE
    layername = 'ne_110m_populated_places'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def empty_table():
    file_path = 'sample/layman.layer/empty.shp'
    workspace = WORKSPACE
    layername = 'empty'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


@pytest.fixture()
def single_point_table():
    file_path = 'sample/layman.layer/single_point.shp'
    workspace = WORKSPACE
    layername = 'single_point'
    post_layer(workspace, layername, file_path)
    yield workspace, layername
    delete_layer(workspace, layername, )


def test_abort_import_layer_vector_file():
    workspace = 'testuser1'
    layername = 'ne_10m_admin_0_countries'
    src_dir = 'tmp/naturalearth/10m/cultural'
    with layman.app_context():
        input_file_dir = ensure_layer_input_file_dir(workspace, layername)
    filename = layername + '.geojson'
    main_filepath = os.path.join(input_file_dir, filename)

    crs_id = None
    shutil.copy(
        os.path.join(src_dir, filename),
        input_file_dir
    )

    def abort_layer_import():
        process = db.import_layer_vector_file_async(workspace, layername, main_filepath,
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
        layerdir = get_layer_dir(workspace, layername)
    shutil.rmtree(layerdir)


def test_data_language(boundary_table):
    workspace, layername = boundary_table
    # print(f"username={username}, layername={layername}")
    with layman.app_context():
        col_names = db.get_text_column_names(workspace, layername)
    assert set(col_names) == set(['featurecla', 'name', 'name_alt'])
    with layman.app_context():
        text_data, _ = db.get_text_data(workspace, layername)
    # print(f"num_rows={num_rows}")
    assert len(text_data) == 1
    assert text_data[0].startswith(' '.join(['International boundary (verify)'] * 100))
    with layman.app_context():
        langs = db.get_text_languages(workspace, layername)
    assert langs == ['eng']


def test_data_language_roads(road_table):
    workspace, layername = road_table
    # print(f"username={username}, layername={layername}")
    with layman.app_context():
        col_names = db.get_text_column_names(workspace, layername)
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
        langs = db.get_text_languages(workspace, layername)
    assert langs == ['cze']


def test_populated_places_table(populated_places_table):
    workspace, layername = populated_places_table
    print(f"workspace={workspace}, layername={layername}")
    with layman.app_context():
        col_names = db.get_text_column_names(workspace, layername)
    assert len(col_names) == 31
    with layman.app_context():
        langs = db.get_text_languages(workspace, layername)
    assert set(langs) == set(['chi', 'eng', 'rus'])


def test_data_language_countries(country_table):
    workspace, layername = country_table
    # print(f"username={username}, layername={layername}")
    with layman.app_context():
        col_names = db.get_text_column_names(workspace, layername)
    assert len(col_names) == 63
    with layman.app_context():
        langs = db.get_text_languages(workspace, layername)
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


def test_data_language_countries2(country110m_table):
    workspace, layername = country110m_table
    # print(f"username={username}, layername={layername}")
    # col_names = db.get_text_column_names(username, layername)
    # print(col_names)
    # assert len(col_names) == 63
    with layman.app_context():
        langs = db.get_text_languages(workspace, layername)
    assert set(langs) == set(['eng'])


def test_get_most_frequent_lower_distance(country110m_table, country50m_table, country10m_table,
                                          data200road_table, sm5building_table):
    _, layername_110m = country110m_table
    _, layername_50m = country50m_table
    _, layername_10m = country10m_table
    _, layername_200k = data200road_table
    workspace, layername_5k = sm5building_table
    with layman.app_context():
        sd_110m = db.guess_scale_denominator(workspace, layername_110m)
    assert 25000000 <= sd_110m <= 500000000
    assert sd_110m == 100000000
    with layman.app_context():
        sd_50m = db.guess_scale_denominator(workspace, layername_50m)
    assert 10000000 <= sd_50m <= 250000000
    assert sd_50m == 10000000
    with layman.app_context():
        sd_10m = db.guess_scale_denominator(workspace, layername_10m)
    assert 2500000 <= sd_10m <= 50000000
    assert sd_10m == 2500000
    with layman.app_context():
        sd_200k = db.guess_scale_denominator(workspace, layername_200k)
    assert 50000 <= sd_200k <= 1000000
    assert sd_200k == 100000
    with layman.app_context():
        sd_5k = db.guess_scale_denominator(workspace, layername_5k)
    assert 1000 <= sd_5k <= 25000
    assert sd_5k == 5000


def test_empty_table_bbox(empty_table):
    workspace, layername = empty_table
    with layman.app_context():
        bbox = db.get_bbox(workspace, layername)
    assert bbox_util.is_empty(bbox), bbox


def test_single_point_table_bbox(single_point_table):
    workspace, layername = single_point_table
    with layman.app_context():
        bbox = db.get_bbox(workspace, layername)
    assert bbox[0] == bbox[2] and bbox[1] == bbox[3], bbox
