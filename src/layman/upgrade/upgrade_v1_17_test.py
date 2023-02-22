import pytest
from werkzeug.datastructures import FileStorage

import crs as crs_def
from db import util as db_util, TableUri
from layman import app, settings, util as layman_util
from layman.common.prime_db_schema import publications as prime_db_schema_publications
from layman.common.filesystem import uuid as uuid_common
from layman.layer import LAYER_TYPE, STYLE_TYPES_DEF, db, geoserver, qgis
from layman.layer.db import table
from layman.layer.geoserver import wms, wfs
from layman.layer.filesystem import input_file, util as fs_util, input_style, thumbnail
from layman.layer.prime_db_schema import table as prime_db_schema_table
from layman.layer.qgis import util as qgis_util, wms as qgis_wms
from layman.uuid import generate_uuid
from test_tools import process_client, geoserver_client
from tests.asserts.final.publication import internal as asserts_internal
from . import upgrade_v1_17, upgrade_v1_20

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
    ALTER TABLE {DB_SCHEMA}.publications DROP COLUMN geodata_type;
    '''
    with app.app_context():
        db_util.run_statement(query)

    # assert DB is in 1.16 state

    query = f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='{DB_SCHEMA}' and table_name='publications' and column_name='geodata_type';
    """
    with app.app_context():
        result = db_util.run_query(query)
    assert len(result) == 0

    # migrate to v1.17

    with app.app_context():
        upgrade_v1_17.adjust_db_for_file_type()
        upgrade_v1_20.rename_file_type_to_geodata_type()
        upgrade_v1_17.adjust_publications_file_type()
        upgrade_v1_17.adjust_db_publication_file_type_constraint()

    # test DB records were migrated to v1.17

    with app.app_context():
        prime_db_schema_infos = prime_db_schema_publications.get_publication_infos(workspace_name=main_workspace)
    assert len(prime_db_schema_infos) == len(publication_defs)
    assert prime_db_schema_infos[vector_layer_def[:3]]['geodata_type'] == 'vector'
    assert prime_db_schema_infos[raster_layer_def[:3]]['geodata_type'] == 'raster'
    assert prime_db_schema_infos[map_def[:3]]['geodata_type'] is None

    layer_infos = process_client.get_workspace_layers(main_workspace)
    assert len(layer_infos) == 2
    vector_layer_info = next(info for info in layer_infos if info['name'] == vector_layer_def[2])
    assert vector_layer_info['file']['file_type'] == 'vector'
    raster_layer_info = next(info for info in layer_infos if info['name'] == raster_layer_def[2])
    assert raster_layer_info['file']['file_type'] == 'raster'

    map_infos = process_client.get_workspace_maps(main_workspace)
    assert len(map_infos) == 1
    for map_info in map_infos:
        assert 'geodata_type' not in map_info

    # clean data

    for workspace, publication_type, publication, _ in publication_defs:
        process_client.delete_workspace_publication(publication_type, workspace, publication)


def publish_layer(workspace, layer, *, file_path, style_type, style_file, ):
    access_rights = {'read': [settings.RIGHTS_EVERYONE_ROLE], 'write': [settings.RIGHTS_EVERYONE_ROLE], }
    with app.app_context():
        uuid_str = generate_uuid()
        with open(file_path, 'rb') as file:
            file = FileStorage(file)
            input_files = fs_util.InputFiles(sent_streams=[file])
            input_file.save_layer_files(
                workspace, layer, input_files, check_crs=True, overview_resampling=None)

        style_type_def = next(iter([std for std in STYLE_TYPES_DEF if std.code == style_type]))
        with open(style_file, 'rb') as file:
            file = FileStorage(file)
            input_style.save_layer_file(workspace, layer, file, style_type_def)
        prime_db_schema_table.post_layer(workspace,
                                         layer,
                                         access_rights=access_rights,
                                         title=layer,
                                         uuid=uuid_str,
                                         actor_name=None,
                                         geodata_type=settings.GEODATA_TYPE_VECTOR,
                                         style_type=style_type_def,
                                         image_mosaic=False,
                                         external_table_uri=None
                                         )
        uuid_common.assign_publication_uuid(LAYER_TYPE, workspace, layer, uuid_str=uuid_str)

        table_name = layer

        db.ensure_workspace(workspace)
        file_info = input_file.get_layer_info(workspace, layer)
        main_filepath = next(iter(file_info['_file']['paths'].values()))['absolute']
        process = db.import_layer_vector_file_to_internal_table_async(workspace, table_name, main_filepath, crs_id=None)
        while process.poll() is None:
            pass
        return_code = process.poll()
        output = process.stdout.read()
        if return_code != 0 or output:
            info = table.get_layer_info(workspace, layer)
            assert info

        bbox = db.get_bbox(workspace, table_name)
        crs = db.get_crs(workspace, table_name, use_internal_srid=True)

        prime_db_schema_publications.set_bbox(workspace, LAYER_TYPE, layer, bbox, crs, )
        if crs_def.CRSDefinitions[crs].internal_srid:
            table.set_internal_table_layer_srid(workspace, table_name, crs_def.CRSDefinitions[crs].internal_srid)

        wms_workspace = wms.get_geoserver_workspace(workspace)

        geoserver.ensure_workspace(workspace)
        geoserver.ensure_workspace(wms_workspace)

        # import into GS WFS workspace
        geoserver.publish_layer_from_db(workspace,
                                        layer,
                                        description=layer,
                                        title=layer,
                                        crs=crs,
                                        table_name=table_name,
                                        geoserver_workspace=workspace,
                                        )

        # import into GS WMS workspace
        if style_type == 'sld':
            geoserver.publish_layer_from_db(workspace,
                                            layer,
                                            description=layer,
                                            title=layer,
                                            crs=crs,
                                            table_name=table_name,
                                            geoserver_workspace=wms_workspace,
                                            )
        elif style_type == 'qml':
            qgis.ensure_layer_dir(workspace, layer)
            qml = qgis_util.get_original_style_xml(workspace, layer)
            qml_geometry = qgis_util.get_qml_geometry_from_qml(qml)
            db_types = db.get_geometry_types(workspace, table_name)
            db_cols = [
                col for col in db.get_all_column_infos(workspace, table_name)
                if col.name not in [settings.OGR_DEFAULT_GEOMETRY_COLUMN, settings.OGR_DEFAULT_PRIMARY_KEY]
            ]
            source_type = qgis_util.get_source_type(db_types, qml_geometry)
            table_uri = TableUri(db_uri_str=settings.PG_URI_STR, table=table_name, schema=workspace,
                                 geo_column=settings.OGR_DEFAULT_GEOMETRY_COLUMN,
                                 primary_key_column=settings.OGR_DEFAULT_PRIMARY_KEY)
            layer_qml = qgis_util.fill_layer_template(layer, uuid_str, bbox, crs, qml, source_type, db_cols, table_uri)
            qgs_str = qgis_util.fill_project_template(layer, uuid_str, layer_qml, crs, settings.LAYMAN_OUTPUT_SRS_LIST,
                                                      bbox, source_type, table_uri)
            with open(qgis_wms.get_layer_file_path(workspace, layer), "w") as qgs_file:
                print(qgs_str, file=qgs_file)

            geoserver.publish_layer_from_qgis(workspace,
                                              layer,
                                              description=layer,
                                              title=layer,
                                              geoserver_workspace=wms_workspace,
                                              )
        for gs_workspace in [workspace, wms.get_geoserver_workspace(workspace)]:
            wms.clear_cache(gs_workspace)
            wfs.clear_cache(gs_workspace)
    return uuid_str


def table_exists(schema, table_name):
    query = f"""
SELECT count(*)
FROM information_schema.tables
WHERE table_schema = %s
AND table_name = %s
"""
    with app.app_context():
        result = db_util.run_query(query, (schema, table_name))
    return result[0][0] == 1


def assert_publication(workspace, layer, *, exp_table_name, exp_non_existing_table_name, exp_thumbnail):
    assert table_exists(schema=workspace, table_name=exp_table_name)
    assert not table_exists(schema=workspace, table_name=exp_non_existing_table_name)

    with app.app_context():
        layer_info = layman_util.get_publication_info(workspace, process_client.LAYER_TYPE, layer,
                                                      context={'keys': ['wms', 'wfs']})
    assert 'wms' in layer_info, f'layer_info={layer_info}'
    assert 'url' in layer_info['wms'], f'layer_info={layer_info}'
    assert 'url' in layer_info['_wms'], f'layer_info={layer_info}'
    assert 'wfs' in layer_info, f'layer_info={layer_info}'
    assert 'url' in layer_info['wfs'], f'layer_info={layer_info}'
    features = geoserver_client.get_features(workspace, layer, )
    assert features
    with app.app_context():
        thumbnail.delete_layer(workspace, layer)
        thumbnail.generate_layer_thumbnail(workspace, layer)
    asserts_internal.thumbnail_equals(workspace, process_client.LAYER_TYPE, layer, exp_thumbnail)


@pytest.mark.usefixtures('ensure_layman')
def test_table_name_migration():
    workspace = 'test_table_name_migration'

    layer_vector_sld = 'test_vector_layer_sld'
    layer_vector_qml = 'test_vector_layer_qml'

    sld_uuid = publish_layer(workspace=workspace,
                             layer=layer_vector_sld,
                             file_path='sample/layman.layer/small_layer.geojson',
                             style_type='sld',
                             style_file='sample/style/basic.sld')
    qml_uuid = publish_layer(workspace=workspace,
                             layer=layer_vector_qml,
                             file_path='sample/layman.layer/small_layer.geojson',
                             style_type='qml',
                             style_file='sample/style/small_layer.qml')

    exp_sld_table_name = f'layer_{sld_uuid.replace("-", "_")}'
    exp_qml_table_name = f'layer_{qml_uuid.replace("-", "_")}'

    assert_publication(workspace, layer_vector_sld,
                       exp_table_name=layer_vector_sld,
                       exp_non_existing_table_name=exp_sld_table_name,
                       exp_thumbnail='sample/style/basic_sld.png')
    assert_publication(workspace, layer_vector_qml,
                       exp_table_name=layer_vector_qml,
                       exp_non_existing_table_name=exp_qml_table_name,
                       exp_thumbnail='sample/style/small_layer_qml.png')

    with app.app_context():
        upgrade_v1_17.rename_table_names()

    assert_publication(workspace, layer_vector_sld,
                       exp_table_name=exp_sld_table_name,
                       exp_non_existing_table_name=layer_vector_sld,
                       exp_thumbnail='sample/style/basic_sld.png')
    assert_publication(workspace, layer_vector_qml,
                       exp_table_name=exp_qml_table_name,
                       exp_non_existing_table_name=layer_vector_qml,
                       exp_thumbnail='sample/style/small_layer_qml.png')

    process_client.delete_workspace_publication(process_client.LAYER_TYPE, workspace, layer_vector_sld)
    process_client.delete_workspace_publication(process_client.LAYER_TYPE, workspace, layer_vector_qml)
