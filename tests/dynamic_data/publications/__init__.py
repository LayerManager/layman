import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
from test_tools import process_client
from . import wrong_input, file_input, celery, common_publications as publications, geoserver_proxy, crs
from .. import predefined_actions
from ... import Action, Publication, dynamic_data as consts


PUBLICATIONS = {
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'basic_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, publications.SMALL_LAYER.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SMALL_LAYER.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, publications.SMALL_LAYER_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SMALL_LAYER_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SMALL_LAYER_ZIP.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_shp_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_tif_tfw_rgba_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, publications.SMALL_LAYER_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **publications.SMALL_LAYER_ZIP.info_values,
                    'exp_publication_detail': {
                        **publications.SMALL_LAYER_ZIP.info_values['exp_publication_detail'],
                        '_file': {
                            'paths': ['/layman_data_test/workspaces/dynamic_test_workspace/layers/zipped_tif_tfw_rgba_opaque/input_file/zipped_tif_tfw_rgba_opaque.zip/small_layer.geojson']
                        },
                        'file': {
                            'path': 'layers/zipped_tif_tfw_rgba_opaque/input_file/zipped_tif_tfw_rgba_opaque.zip/small_layer.geojson'
                        },
                    },
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SMALL_LAYER_ZIP.thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_tif_colortable_nodata_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **publications.SMALL_LAYER_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SMALL_LAYER_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SMALL_LAYER_ZIP.thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_shp_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **publications.SMALL_LAYER_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SMALL_LAYER_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SMALL_LAYER_ZIP.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_tif_tfw_rgba_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_tif_colortable_nodata_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_shp_without_prj'): [
        {
            consts.KEY_ACTION: predefined_actions.POST_ZIP_SHP_WITHOUT_PRJ_WITH_CRS,
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.info_values,
                    'file_extension': 'zip/ne_110m_admin_0_boundary_lines_land.shp',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_zip_and_main_file'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'tmp/sm5/vektor/sm5.zip',
                        'sample/layman.layer/small_layer.geojson',
                    ],
                    'compress': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **publications.SMALL_LAYER.info_values,
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'without_explicit_name'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'name': None,
                    'file_paths': ['sample/layman.layer/small_layer.geojson'],
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {'name': 'small_layer'}),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.source_has_its_key_or_it_is_empty, {'name': 'small_layer'}),
                Action(publication.internal.source_internal_keys_are_subset_of_source_sibling_keys, {'name': 'small_layer'}),
                Action(publication.internal_rest.same_title_in_source_and_rest_multi, {'name': 'small_layer'}),
                Action(publication.internal_rest.same_values_in_internal_and_rest, {'name': 'small_layer'}),
                Action(publication.rest.is_in_rest_multi, {'name': 'small_layer'}),
                Action(publication.rest.correct_url_in_rest_multi, {'name': 'small_layer'}),
                Action(publication.internal.same_value_of_key_in_all_sources, {'name': 'small_layer'}),
                Action(publication.internal.mandatory_keys_in_all_sources, {'name': 'small_layer'}),
                Action(publication.internal.all_keys_assigned_to_source, {'name': 'small_layer'}),
                Action(publication.internal.metadata_key_sources_do_not_contain_other_keys, {'name': 'small_layer'}),
                Action(publication.internal.thumbnail_key_sources_do_not_contain_other_keys, {'name': 'small_layer'}),
                Action(publication.internal.mandatory_keys_in_primary_db_schema_of_actor, {'name': 'small_layer'}),
                Action(publication.internal.other_keys_not_in_primary_db_schema_of_actor, {'name': 'small_layer'}),
                Action(publication.internal.mandatory_keys_in_all_sources_of_actor, {'name': 'small_layer'}),
                Action(publication.rest.is_complete_in_rest, {'name': 'small_layer'}),
                Action(publication.rest.mandatory_keys_in_rest, {'name': 'small_layer'}),
                Action(publication.geoserver.workspace_wms_1_3_0_capabilities_available, {'name': 'small_layer'}),
                Action(publication.geoserver.workspace_wfs_2_0_0_capabilities_available_if_vector, {'name': 'small_layer'}),
                Action(publication.internal.correct_values_in_detail, {
                    **publications.SMALL_LAYER.info_values,
                    'name': 'small_layer',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'name': 'small_layer',
                    'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zip_without_explicit_name'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'name': None,
                    'file_paths': ['sample/layman.layer/small_layer_with_id.geojson'],
                    'compress': True,
                    'compress_settings': process_client.CompressTypeDef(archive_name='small_zip_layer'),
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {'name': 'small_layer_with_id'}),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.source_has_its_key_or_it_is_empty, {'name': 'small_layer_with_id'}),
                Action(publication.internal.source_internal_keys_are_subset_of_source_sibling_keys, {'name': 'small_layer_with_id'}),
                Action(publication.internal_rest.same_title_in_source_and_rest_multi, {'name': 'small_layer_with_id'}),
                Action(publication.internal_rest.same_values_in_internal_and_rest, {'name': 'small_layer_with_id'}),
                Action(publication.rest.is_in_rest_multi, {'name': 'small_layer_with_id'}),
                Action(publication.rest.correct_url_in_rest_multi, {'name': 'small_layer_with_id'}),
                Action(publication.internal.same_value_of_key_in_all_sources, {'name': 'small_layer_with_id'}),
                Action(publication.internal.mandatory_keys_in_all_sources, {'name': 'small_layer_with_id'}),
                Action(publication.internal.all_keys_assigned_to_source, {'name': 'small_layer_with_id'}),
                Action(publication.internal.metadata_key_sources_do_not_contain_other_keys, {'name': 'small_layer_with_id'}),
                Action(publication.internal.thumbnail_key_sources_do_not_contain_other_keys, {'name': 'small_layer_with_id'}),
                Action(publication.internal.mandatory_keys_in_primary_db_schema_of_actor, {'name': 'small_layer_with_id'}),
                Action(publication.internal.other_keys_not_in_primary_db_schema_of_actor, {'name': 'small_layer_with_id'}),
                Action(publication.internal.mandatory_keys_in_all_sources_of_actor, {'name': 'small_layer_with_id'}),
                Action(publication.rest.is_complete_in_rest, {'name': 'small_layer_with_id'}),
                Action(publication.rest.mandatory_keys_in_rest, {'name': 'small_layer_with_id'}),
                Action(publication.geoserver.workspace_wms_1_3_0_capabilities_available, {'name': 'small_layer_with_id'}),
                Action(publication.geoserver.workspace_wfs_2_0_0_capabilities_available_if_vector, {'name': 'small_layer_with_id'}),
                Action(publication.internal.correct_values_in_detail, {
                    **publications.SMALL_LAYER.info_values,
                    'name': 'small_layer_with_id',
                    'file_extension': 'zip/small_layer_with_id.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'name': 'small_layer_with_id',
                    'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zip_chunks_without_explicit_name'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'name': None,
                    'file_paths': ['sample/layman.layer/small_layer.geojson'],
                    'compress': True,
                    'compress_settings': process_client.CompressTypeDef(archive_name='small_zip_layer'),
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {'name': 'small_zip_layer'}),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.source_has_its_key_or_it_is_empty, {'name': 'small_zip_layer'}),
                Action(publication.internal.source_internal_keys_are_subset_of_source_sibling_keys, {'name': 'small_zip_layer'}),
                Action(publication.internal_rest.same_title_in_source_and_rest_multi, {'name': 'small_zip_layer'}),
                Action(publication.internal_rest.same_values_in_internal_and_rest, {'name': 'small_zip_layer'}),
                Action(publication.rest.is_in_rest_multi, {'name': 'small_zip_layer'}),
                Action(publication.rest.correct_url_in_rest_multi, {'name': 'small_zip_layer'}),
                Action(publication.internal.same_value_of_key_in_all_sources, {'name': 'small_zip_layer'}),
                Action(publication.internal.mandatory_keys_in_all_sources, {'name': 'small_zip_layer'}),
                Action(publication.internal.all_keys_assigned_to_source, {'name': 'small_zip_layer'}),
                Action(publication.internal.metadata_key_sources_do_not_contain_other_keys, {'name': 'small_zip_layer'}),
                Action(publication.internal.thumbnail_key_sources_do_not_contain_other_keys, {'name': 'small_zip_layer'}),
                Action(publication.internal.mandatory_keys_in_primary_db_schema_of_actor, {'name': 'small_zip_layer'}),
                Action(publication.internal.other_keys_not_in_primary_db_schema_of_actor, {'name': 'small_zip_layer'}),
                Action(publication.internal.mandatory_keys_in_all_sources_of_actor, {'name': 'small_zip_layer'}),
                Action(publication.rest.is_complete_in_rest, {'name': 'small_zip_layer'}),
                Action(publication.rest.mandatory_keys_in_rest, {'name': 'small_zip_layer'}),
                Action(publication.geoserver.workspace_wms_1_3_0_capabilities_available, {'name': 'small_zip_layer'}),
                Action(publication.geoserver.workspace_wfs_2_0_0_capabilities_available_if_vector, {'name': 'small_zip_layer'}),
                Action(publication.internal.correct_values_in_detail, {
                    **publications.SMALL_LAYER.info_values,
                    'name': 'small_zip_layer',
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'name': 'small_zip_layer',
                    'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
                }),
            ],
        },
    ],
    **wrong_input.generate(consts.COMMON_WORKSPACE + '_generated_wrong_input'),
    **file_input.generate(consts.COMMON_WORKSPACE + '_generated_file_input'),
    **celery.generate(consts.COMMON_WORKSPACE + '_celery'),
    **geoserver_proxy.generate(consts.COMMON_WORKSPACE + '_geoserver_proxy'),
    **crs.generate(consts.COMMON_WORKSPACE + '_crs'),
}

# pylint: disable=unnecessary-comprehension
PUBLICATIONS = {
    publ: definition
    for publ, definition in PUBLICATIONS.items()
    # if publ.workspace == consts.COMMON_WORKSPACE
    #    and publ.name in ('zipped_tif_tfw_rgba_opaque')
}
