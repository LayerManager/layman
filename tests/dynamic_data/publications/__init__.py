from tests.asserts.final import publication
from tests.asserts import processing
from test_tools import process_client
from . import common_publications as publications
from .. import predefined_actions
from ... import Action, Publication4Test, dynamic_data as consts


PUBLICATIONS = {
    Publication4Test(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_shp_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {}),
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
    Publication4Test(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_tif_tfw_rgba_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {}),
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
                    Action(processing.response.valid_post, {}),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **publications.SMALL_LAYER_ZIP.info_values,
                    'exp_publication_detail': {
                        **publications.SMALL_LAYER_ZIP.info_values['exp_publication_detail'],
                    },
                    'file_extension': 'zip/small_layer.geojson',
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
                    Action(processing.response.valid_post, {}),
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
                    Action(processing.response.valid_post, {}),
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
                    Action(processing.response.valid_post, {}),
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
    Publication4Test(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_tif_colortable_nodata_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {}),
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
    Publication4Test(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **publications.SMALL_LAYER_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {}),
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
                    Action(processing.response.valid_post, {}),
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
    Publication4Test(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_shp_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {}),
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
                    Action(processing.response.valid_post, {}),
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
    Publication4Test(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_tif_tfw_rgba_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **publications.SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {}),
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
                    Action(processing.response.valid_post, {}),
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
    Publication4Test(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_tif_colortable_nodata_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP.definition,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {}),
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
                    Action(processing.response.valid_post, {}),
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
    Publication4Test(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_shp_without_prj'): [
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
}

# pylint: disable=unnecessary-comprehension
PUBLICATIONS = {
    publ: definition
    for publ, definition in PUBLICATIONS.items()
    # if publ.workspace == consts.COMMON_WORKSPACE
    #    and publ.name in ('zipped_tif_tfw_rgba_opaque')
}
