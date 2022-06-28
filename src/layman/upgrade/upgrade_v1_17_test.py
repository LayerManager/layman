import pytest

from db import util as db_util
from layman import app, settings
from layman.common.prime_db_schema import publications as prime_db_schema_publications
from test_tools import process_client
from . import upgrade_v1_17

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman')
def test_file_type():

    main_workspace = 'test_file_type_workspace'

    vector_layer_def = (main_workspace, process_client.LAYER_TYPE, 'test_vector_layer', {'file_paths': [
        'sample/layman.layer/small_layer.cpg',
        'sample/layman.layer/small_layer.dbf',
        'sample/layman.layer/small_layer.prj',
        'sample/layman.layer/small_layer.shp',
        'sample/layman.layer/small_layer.shx',
    ], },)
    raster_layer_def = (main_workspace, process_client.LAYER_TYPE, 'test_raster_layer', {'file_paths': [
        'sample/layman.layer/sample_tif_rgb.tif',
    ], },)
    map_def = (main_workspace, process_client.MAP_TYPE, 'test_map', dict(),)

    publication_defs = [vector_layer_def, raster_layer_def, map_def]

    for workspace, publication_type, publication, params in publication_defs:
        process_client.publish_workspace_publication(publication_type, workspace, publication, **params)

    # put DB to v1.16 state

    query = f'''
    ALTER TABLE {DB_SCHEMA}.publications DROP CONSTRAINT file_type_with_publ_type_check;
    ALTER TABLE {DB_SCHEMA}.publications DROP COLUMN file_type;
    '''
    with app.app_context():
        db_util.run_statement(query)

    # assert DB is in 1.16 state

    query = f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='{DB_SCHEMA}' and table_name='publications' and column_name='file_type';
    """
    with app.app_context():
        result = db_util.run_query(query)
    assert len(result) == 0

    # migrate to v1.17

    with app.app_context():
        upgrade_v1_17.adjust_db_for_file_type()
        upgrade_v1_17.adjust_publications_file_type()
        upgrade_v1_17.adjust_db_publication_file_type_constraint()

    # test DB records were migrated to v1.17

    with app.app_context():
        prime_db_schema_infos = prime_db_schema_publications.get_publication_infos(workspace_name=main_workspace)
    assert len(prime_db_schema_infos) == len(publication_defs)
    assert prime_db_schema_infos[vector_layer_def[:3]]['file_type'] == 'vector'
    assert prime_db_schema_infos[raster_layer_def[:3]]['file_type'] == 'raster'
    assert prime_db_schema_infos[map_def[:3]]['file_type'] is None

    layer_infos = process_client.get_workspace_layers(main_workspace)
    assert len(layer_infos) == 2
    vector_layer_info = next(info for info in layer_infos if info['name'] == vector_layer_def[2])
    assert vector_layer_info['file_type'] == 'vector'
    raster_layer_info = next(info for info in layer_infos if info['name'] == raster_layer_def[2])
    assert raster_layer_info['file_type'] == 'raster'

    map_infos = process_client.get_workspace_maps(main_workspace)
    assert len(map_infos) == 1
    for map_info in map_infos:
        assert 'file_type' not in map_info

    # clean data

    for workspace, publication_type, publication, _ in publication_defs:
        process_client.delete_workspace_publication(publication_type, workspace, publication)
