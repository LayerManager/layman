import os
import shutil
import pytest
import time

import sys
del sys.modules['layman']

from layman import app as layman, settings
from layman.layer.filesystem.input_file import ensure_layer_input_file_dir
from layman.layer.filesystem.util import get_layer_dir
from layman.layer import db
from .table import delete_layer


@pytest.fixture(scope="module")
def client():
    layman.config['TESTING'] = True
    layman.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    layman.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME
    client = layman.test_client()

    with layman.app_context() as ctx:
        yield client
        pass


@pytest.fixture(scope="module")
def testuser1():
    username = 'db_testuser'
    db.ensure_user_workspace(username)
    yield username
    db.delete_user_workspace(username)


@pytest.fixture()
def boundary_table(testuser1):
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp'
    username = testuser1
    layername = 'hranice'
    db.import_layer_vector_file(username, layername, file_path, None)
    yield username, layername
    delete_layer(username, layername)


@pytest.fixture()
def road_table(testuser1):
    file_path = 'sample/data/upper_attr.geojson'
    username = testuser1
    layername = 'silnice'
    db.import_layer_vector_file(username, layername, file_path, None)
    yield username, layername
    delete_layer(username, layername)


@pytest.fixture()
def country_table(testuser1):
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp'
    username = testuser1
    layername = 'staty'
    db.import_layer_vector_file(username, layername, file_path, None)
    yield username, layername
    delete_layer(username, layername)


@pytest.fixture()
def country2_table(testuser1):
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'
    username = testuser1
    layername = 'staty2'
    db.import_layer_vector_file(username, layername, file_path, None)
    yield username, layername
    delete_layer(username, layername)


@pytest.fixture()
def populated_places_table(testuser1):
    file_path = 'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson'
    username = testuser1
    layername = 'ne_110m_populated_places'
    db.import_layer_vector_file(username, layername, file_path, None)
    yield username, layername
    delete_layer(username, layername)


def test_abort_import_layer_vector_file(client):
    username = 'testuser1'
    layername = 'ne_10m_admin_0_countries'
    src_dir = 'tmp/naturalearth/10m/cultural'
    input_file_dir = ensure_layer_input_file_dir(username, layername)
    filename = layername+'.geojson'
    main_filepath = os.path.join(input_file_dir, filename)

    crs_id = None
    shutil.copy(
        os.path.join(src_dir, filename),
        input_file_dir
    )

    def abort_layer_import():
        p = db.import_layer_vector_file_async(username, layername, main_filepath,
                                        crs_id)
        time1 = time.time()
        while p.poll() is None:
            if(time.time()-time1 > 0.1):
                # print('terminating process')
                p.terminate()
            time.sleep(0.1)
            pass

        return_code = p.poll()
        return return_code

    return_code = abort_layer_import()
    assert return_code != 0
    layerdir = get_layer_dir(username, layername)
    shutil.rmtree(layerdir)


def test_data_language(client, boundary_table):
    username, layername = boundary_table
    # print(f"username={username}, layername={layername}")
    col_names = db.get_text_column_names(username, layername)
    assert set(col_names) == set(['featurecla', 'name', 'name_alt'])
    text_data, num_rows = db.get_text_data(username, layername)
    # print(f"num_rows={num_rows}")
    assert len(text_data) == 1
    assert text_data[0].startswith(' '.join(['International boundary (verify)']*100))
    langs = db.get_text_languages(username, layername)
    assert langs == ['eng']


def test_data_language_roads(road_table):
    username, layername = road_table
    # print(f"username={username}, layername={layername}")
    col_names = db.get_text_column_names(username, layername)
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
    langs = db.get_text_languages(username, layername)
    assert langs == ['cze']


def test_populated_places_table(client, populated_places_table):
    username, layername = populated_places_table
    print(f"username={username}, layername={layername}")
    col_names = db.get_text_column_names(username, layername)
    assert len(col_names) == 31
    langs = db.get_text_languages(username, layername)
    assert set(langs) == set(['chi', 'eng', 'rus'])


def test_data_language_countries(country_table):
    username, layername = country_table
    # print(f"username={username}, layername={layername}")
    col_names = db.get_text_column_names(username, layername)
    assert len(col_names) == 63
    langs = db.get_text_languages(username, layername)
    assert set(langs) == set([
        'ara',
        'ben',
        'chi',
        'dut',
        'eng',
        'fre',
        'ger',
        'gre',
        'hin',
        'hun',
        'jpn',
        'kor',
        'pol',
        'rus',
        'spa',
        'vie',
    ])



def test_data_language_countries2(country2_table):
    username, layername = country2_table
    # print(f"username={username}, layername={layername}")
    # col_names = db.get_text_column_names(username, layername)
    # print(col_names)
    # assert len(col_names) == 63
    langs = db.get_text_languages(username, layername)
    assert set(langs) == set(['eng'])



