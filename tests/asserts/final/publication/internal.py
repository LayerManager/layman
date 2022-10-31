import os

import pytest
from db import util as db_util
from layman import app, util as layman_util, settings, celery
from layman.common import bbox as bbox_util
from layman.common.prime_db_schema import publications
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from layman.layer.filesystem import gdal
from test_tools import process_client, util as test_util, assert_util
from ... import util


def source_has_its_key_or_it_is_empty(workspace, publ_type, name):
    with app.app_context():
        all_items = layman_util.get_publication_types()[publ_type]['internal_sources'].values()
        for source_def in all_items:
            for key in source_def.info_items:
                context = {'keys': [key]}
                info = layman_util.get_publication_info(workspace, publ_type, name, context)
                assert key in info or f'_{key}' in info or not info, info


def source_internal_keys_are_subset_of_source_sibling_keys(workspace, publ_type, name):
    with app.app_context():
        internal_sources = layman_util.get_publication_types()[publ_type]['internal_sources']
        for source_name, source_def in internal_sources.items():
            for key in source_def.info_items:
                context = {'keys': [key]}
                info = layman_util.get_publication_info(workspace, publ_type, name, context)
                all_sibling_keys = set(sibling_key
                                       for item_list in internal_sources.values()
                                       for sibling_key in item_list.info_items
                                       if key in item_list.info_items)
                internal_keys = [key[1:] for key in info if key.startswith('_')]
                if publ_type == MAP_TYPE and source_name == 'layman.map.prime_db_schema.table':
                    internal_keys.remove('style_type')
                    internal_keys.remove('file_type')
                assert set(internal_keys) <= all_sibling_keys, \
                    f'internal_keys={set(internal_keys)}, all_sibling_keys={all_sibling_keys}, key={key}, info={info}'


def same_value_of_key_in_all_sources(workspace, publ_type, name):
    with app.app_context():
        sources = layman_util.get_internal_sources(publ_type)
        info = layman_util.get_publication_info(workspace, publ_type, name)

    info_method = {
        process_client.LAYER_TYPE: 'get_layer_info',
        process_client.MAP_TYPE: 'get_map_info',
    }[publ_type]
    with app.app_context():
        partial_infos = layman_util.call_modules_fn(sources, info_method, [workspace, name])

    for source, source_info in partial_infos.items():
        for key, value in source_info.items():
            if key in info:
                assert_util.assert_same_values_for_keys(expected=info[key],
                                                        tested=value,
                                                        missing_key_is_ok=True,
                                                        path=f'[{source}]',
                                                        )


def mandatory_keys_in_all_sources(workspace, publ_type, name):
    # Items
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name)
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file', }.issubset(set(pub_info)), pub_info


def metadata_key_sources_do_not_contain_other_keys(workspace, publ_type, name):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['metadata']})
    assert {'metadata', }.issubset(set(pub_info)), pub_info
    assert all(item not in pub_info for item in {'name', 'title', 'access_rights', 'uuid', 'file', }), pub_info


def thumbnail_key_sources_do_not_contain_other_keys(workspace, publ_type, name):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['thumbnail']})
    assert {'thumbnail', }.issubset(set(pub_info)), pub_info
    assert all(item not in pub_info for item in {'name', 'title', 'access_rights', 'uuid', 'file', 'metadata', }), pub_info


def mandatory_keys_in_primary_db_schema_of_actor(workspace, publ_type, name, actor, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'actor_name': actor, 'keys': []})
    assert {'name', 'title', 'access_rights', 'uuid', }.issubset(set(pub_info)), pub_info


def other_keys_not_in_primary_db_schema_of_actor(workspace, publ_type, name, actor, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'actor_name': actor, 'keys': []})
    assert all(item not in pub_info for item in {'metadata', 'file', }), pub_info


def mandatory_keys_in_all_sources_of_actor(workspace, publ_type, name, actor, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'actor_name': actor})
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file', }.issubset(set(pub_info)), pub_info


def all_keys_assigned_to_source(workspace, publ_type, name):
    with app.app_context():
        info = layman_util.get_publication_info(workspace, publ_type, name)
        internal_sources = layman_util.get_publication_types()[publ_type]['internal_sources']
    source_keys = set()
    for source_def in internal_sources.values():
        source_keys = source_keys.union(set(source_def.info_items))
    info_keys = {key[1:] if key.startswith('_') else key for key in info}
    if publ_type == MAP_TYPE:
        info_keys.remove('style_type')
        info_keys.remove('file_type')
    assert info_keys.issubset(source_keys), f'missing={info_keys.difference(source_keys)} ,info_keys={info_keys}, source_keys={source_keys}'


def thumbnail_equals(workspace, publ_type, name, exp_thumbnail, *, max_diffs=None):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['thumbnail']})

    diffs = test_util.compare_images(exp_thumbnail, pub_info['_thumbnail']['path'])
    max_diffs = max_diffs or 500
    assert diffs < max_diffs


def correct_values_in_detail(workspace, publ_type, name, *, exp_publication_detail, publ_type_detail=None, full_comparison=True,
                             file_extension=None, gdal_prefix='', keys_to_remove=None, files=None, ):
    assert not file_extension or not files
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name)
    publ_type_dir = util.get_directory_name_from_publ_type(publ_type)
    expected_detail = {
        'name': name,
        'title': name,
        'type': publ_type,
        'thumbnail': {
            'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}/thumbnail',
            'path': f'{publ_type_dir}/{name}/thumbnail/{name}.png'
        },
        'metadata': {
            'comparison_url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}/metadata-comparison',
            'csw_url': 'http://localhost:3080/csw',
        },
        '_thumbnail': {'path': f'/layman_data_test/workspaces/{workspace}/{publ_type_dir}/{name}/thumbnail/{name}.png'},
        'access_rights': {'read': ['EVERYONE'], 'write': ['EVERYONE']},
        'image_mosaic': False,
    }
    if publ_type == process_client.LAYER_TYPE:
        util.recursive_dict_update(expected_detail,
                                   {
                                       'style': {
                                           'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}/style',
                                       },
                                       'wms': {
                                           'url': f'{settings.LAYMAN_GS_PROXY_BASE_URL}{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}/ows'},
                                       '_wms': {
                                           'url': f'{settings.LAYMAN_GS_URL}{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}/ows',
                                           'workspace': f'{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}'},
                                       'description': None,
                                   })

        if file_extension:
            util.recursive_dict_update(expected_detail,
                                       {
                                           '_file': {
                                               'paths': [
                                                   {
                                                       'absolute': f'/layman_data_test/workspaces/{workspace}/{publ_type_dir}/{name}/input_file/{name}.{file_extension}',
                                                       'gdal': f'{gdal_prefix}/layman_data_test/workspaces/{workspace}/{publ_type_dir}/{name}/input_file/{name}.{file_extension}',
                                                   }
                                               ],
                                           },
                                           'file': {
                                               'path': f'{publ_type_dir}/{name}/input_file/{name}.{file_extension}',
                                               'paths': [f'{publ_type_dir}/{name}/input_file/{name}.{file_extension}'],
                                           },
                                       })
        if files:
            util.recursive_dict_update(expected_detail,
                                       {
                                           '_file': {
                                               'paths': [
                                                   {
                                                       'absolute': f'/layman_data_test/workspaces/{workspace}/{publ_type_dir}/{name}/input_file/{filename}',
                                                       'gdal': f'{gdal_prefix}/layman_data_test/workspaces/{workspace}/{publ_type_dir}/{name}/input_file/{filename}',
                                                   }
                                                   for filename in files
                                               ]
                                           },
                                           'file': {
                                               'path': f'{publ_type_dir}/{name}/input_file/{files[0]}',
                                               'paths': [
                                                   f'{publ_type_dir}/{name}/input_file/{filename}'
                                                   for filename in files],
                                           },
                                       })

        file_type = publ_type_detail[0]
        expected_detail['_file_type'] = file_type
        if file_type == settings.FILE_TYPE_VECTOR:
            uuid = pub_info["uuid"]
            db_table = f'layer_{uuid.replace("-","_")}'
            util.recursive_dict_update(expected_detail,
                                       {
                                           'wfs': {'url': f'http://localhost:8000/geoserver/{workspace}/wfs'},
                                           'file': {'file_type': 'vector'},
                                           'db_table': {'name': db_table},
                                       })
        elif file_type == settings.FILE_TYPE_RASTER:
            util.recursive_dict_update(expected_detail,
                                       {
                                           'file': {'file_type': 'raster'},
                                       })
            if file_extension:
                util.recursive_dict_update(expected_detail,
                                           {
                                               '_file': {
                                                   'normalized_file': {
                                                       'paths': [f'/geoserver/data_dir/normalized_raster_data_test/workspaces/{workspace}/{publ_type_dir}/{name}/{name}.tif', ],
                                                       'gs_paths': [f'normalized_raster_data_test/workspaces/{workspace}/{publ_type_dir}/{name}/{name}.tif', ],
                                                   },
                                               },
                                           })
            if files:
                util.recursive_dict_update(expected_detail,
                                           {
                                               '_file': {
                                                   'normalized_file': {
                                                       'paths': [f'/geoserver/data_dir/normalized_raster_data_test/workspaces/{workspace}/{publ_type_dir}/{name}/{os.path.splitext(os.path.basename(filename))[0]}.tif' for filename in files],
                                                       'gs_paths': [f'normalized_raster_data_test/workspaces/{workspace}/{publ_type_dir}/{name}/{os.path.splitext(os.path.basename(filename))[0]}.tif' for filename in files],
                                                   },
                                               },
                                           })
        else:
            raise NotImplementedError(f"Unknown file type: {file_type}")

        style_type = publ_type_detail[1]
        if style_type:
            util.recursive_dict_update(expected_detail,
                                       {
                                           '_style_type': style_type,
                                           'style': {'type': style_type},
                                       })
            if style_type == 'qml':
                util.recursive_dict_update(expected_detail,
                                           {
                                               '_wms': {'qgis_capabilities_url': f'{settings.LAYMAN_QGIS_URL}?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.1.1&map={settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}/{publ_type_dir}/{name}/{name}.qgis'},
                                           })

    if publ_type == process_client.MAP_TYPE:
        expected_detail['_file_type'] = None
        util.recursive_dict_update(expected_detail,
                                   {
                                       '_file': {
                                           'url': f'http://{settings.LAYMAN_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}/file',
                                       },
                                       'file': {
                                           'path': f'{publ_type_dir}/{name}/input_file/{name}.json',
                                           'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}/file'},
                                       '_style_type': None,
                                   })

    expected_detail = util.recursive_dict_update(expected_detail, exp_publication_detail)

    if keys_to_remove:
        for key in keys_to_remove:
            expected_detail.pop(key)

    if full_comparison:
        for key in {'id', 'uuid', 'updated_at', }:
            pub_info.pop(key)
        for key in {'identifier', 'record_url', }:
            pub_info['metadata'].pop(key)
        assert expected_detail == pub_info
    else:
        assert_util.assert_same_values_for_keys(expected=expected_detail,
                                                tested=pub_info,
                                                )


def does_not_exist(workspace, publ_type, name, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name)
    assert not pub_info, pub_info


def nodata_preserved_in_normalized_raster(workspace, publ_type, name):
    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['file']})
    file_type = publ_info['file']['file_type']
    if file_type == settings.FILE_TYPE_RASTER:
        normalized_paths = publ_info['_file']['normalized_file']['paths']
        for idx, file_paths in enumerate(publ_info['_file']['paths']):
            gdal_path = file_paths['gdal']
            input_nodata_value = gdal.get_nodata_value(gdal_path)
            normalized_nodata_value = gdal.get_nodata_value(normalized_paths[idx])
            assert normalized_nodata_value == pytest.approx(input_nodata_value, 0.000000001)


def stats_preserved_in_normalized_raster(workspace, publ_type, name):
    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['file']})
    file_type = publ_info['file']['file_type']
    if file_type == settings.FILE_TYPE_RASTER:
        normalized_paths = publ_info['_file']['normalized_file']['paths']
        for file_idx, file_paths in enumerate(publ_info['_file']['paths']):
            gdal_path = file_paths['gdal']
            normalized_path = normalized_paths[file_idx]
            input_stats = gdal.get_statistics(gdal_path)
            driver_name = gdal.get_driver_short_name(gdal_path)
            tolerance = 0.000000001 if driver_name != 'JPEG' else 0.1
            normalized_stats = gdal.get_statistics(normalized_path)
            for band_idx in range(0, min(len(input_stats), len(normalized_stats))):
                input_band_stats = input_stats[band_idx]
                normalized_band_stats = normalized_stats[band_idx]
                for value_idx, input_value in enumerate(input_band_stats):
                    normalized_value = normalized_band_stats[value_idx]
                    assert input_value == pytest.approx(normalized_value, tolerance), f"band_idx={band_idx}, input_band_stats={input_band_stats}, normalized_band_stats={normalized_band_stats}, tolerance={tolerance}"


def size_and_position_preserved_in_normalized_raster(workspace, publ_type, name):
    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['file']})
    file_type = publ_info['file']['file_type']
    if file_type == settings.FILE_TYPE_RASTER:
        normalized_paths = publ_info['_file']['normalized_file']['paths']
        for file_idx, file_paths in enumerate(publ_info['_file']['paths']):
            gdal_path = file_paths['gdal']
            normalized_path = normalized_paths[file_idx]

            input_raster_size = gdal.get_raster_size(gdal_path)
            normalized_raster_size = gdal.get_raster_size(normalized_path)
            assert input_raster_size == normalized_raster_size, f"input_raster_size={input_raster_size}, normalized_raster_size={normalized_raster_size}"

            input_pixel_size = gdal.get_pixel_size(gdal_path)
            normalized_pixel_size = gdal.get_pixel_size(normalized_path)
            pixel_size_tolerance = 0.000000001
            for value_idx, input_value in enumerate(input_pixel_size):
                normalized_value = normalized_pixel_size[value_idx]
                assert input_value == pytest.approx(normalized_value, pixel_size_tolerance), f"input_pixel_size={input_pixel_size}, normalized_pixel_size={normalized_pixel_size}, tolerance={pixel_size_tolerance}"

            input_bbox = gdal.get_bbox_from_file(gdal_path)
            normalized_bbox = gdal.get_bbox_from_file(normalized_path)
            bbox_tolerance = 0.000000001
            for value_idx, input_value in enumerate(input_bbox):
                normalized_value = normalized_bbox[value_idx]
                assert input_value == pytest.approx(normalized_value, bbox_tolerance), f"input_bbox={input_bbox}, normalized_bbox={normalized_bbox}, tolerance={bbox_tolerance}"


def expected_chain_info_state(workspace, publ_type, name, state):
    chain_info = celery.get_publication_chain_info_dict(workspace, publ_type, name)
    assert chain_info['state'] == state, f'chain_info={chain_info}'


def no_bbox_and_crs(workspace, publ_type, name):
    with app.app_context():
        info = publications.get_publication_infos(workspace_name=workspace, pub_type=publ_type, )
    native_bbox = info[(workspace, publ_type, name)]['native_bounding_box']
    native_crs = info[(workspace, publ_type, name)]['native_crs']

    assert native_bbox == [None, None, None, None]
    assert native_crs is None


def detail_3857bbox_value(workspace, publ_type, name, *, exp_bbox, precision=0.1, contains=True):
    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['bounding_box']})
    bounding_box = publ_info['bounding_box']

    assert_util.assert_same_bboxes(exp_bbox, bounding_box, precision)
    if contains:
        assert bbox_util.contains_bbox(bounding_box, exp_bbox)


def point_coordinates(workspace, publ_type, name, *, point_id, crs, exp_coordinates, precision, ):
    assert publ_type == LAYER_TYPE

    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['db_table']})
    db_table = publ_info['db_table']['name']

    query = f'''with transformed as (select st_transform(wkb_geometry, %s) point
from {workspace}.{db_table}
where point_id = %s)
select st_x(point),
       st_y(point)
from transformed
;'''
    with app.app_context():
        to_srid = db_util.get_srid(crs)
        coordinates = db_util.run_query(query, (to_srid, point_id))
    assert len(coordinates) == 1, coordinates
    coordinates = coordinates[0]

    for i in range(0, 1):
        assert abs(exp_coordinates[i] - coordinates[i]) <= precision, f'exp_coordinates={exp_coordinates}, coordinates={coordinates}'
