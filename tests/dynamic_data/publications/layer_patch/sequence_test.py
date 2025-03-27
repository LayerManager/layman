from copy import deepcopy
from enum import Enum, unique

import pytest

from test_tools import process_client
from tests import EnumTestTypes, Publication4Test
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test
from tests.dynamic_data.base_test_classes import WithChunksDomain, CompressDomain
from tests.dynamic_data.base_test_util import case_to_simple_parametrizations
from tests.dynamic_data.publications import common_publications as publications


pytest_generate_tests = base_test.pytest_generate_tests


@unique
class Key(Enum):
    REST_ARGS = 'rest_args'
    MANDATORY_CASES = 'mandatory_cases'
    RUN_ONLY_CASES = 'run_only_cases'
    EXP_INFO = 'exp_info'
    EXP_THUMBNAIL = 'exp_thumbnail'
    ACTIONS = 'actions'
    ACTION_NAME = 'action_name'


WORKSPACE = 'patch_sequence_ws'
ALL_CASES = frozenset([WithChunksDomain, CompressDomain])

TESTCASES = {
    'geodata_change': {
        Key.RUN_ONLY_CASES: frozenset([WithChunksDomain.FALSE, CompressDomain.TRUE]),
        Key.MANDATORY_CASES: frozenset([WithChunksDomain.FALSE, CompressDomain.TRUE]),
        Key.ACTIONS: [
            {
                Key.ACTION_NAME: 'post-tif-rgba',
                Key.REST_ARGS: {
                    **publications.SAMPLE_TIF_TFW_RGBA_OPAQUE.definition,
                    'compress_settings': process_client.CompressTypeDef(
                        inner_directory='/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/',
                    ),
                },
                Key.EXP_INFO: {
                    **publications.SAMPLE_TIF_TFW_RGBA_OPAQUE.info_values,
                    'file_extension': 'zip/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                },
                Key.EXP_THUMBNAIL: publications.SAMPLE_TIF_TFW_RGBA_OPAQUE.thumbnail,
            },
            {
                Key.ACTION_NAME: 'patch-tif-rgba-to-small-vector',
                Key.REST_ARGS: {
                    **publications.SMALL_LAYER.definition,
                },
                Key.EXP_INFO: publications.SMALL_LAYER_ZIP.info_values,
                Key.EXP_THUMBNAIL: publications.SMALL_LAYER.thumbnail,
            },
            {
                Key.ACTION_NAME: 'patch-small-vector-to-tif-colortable',
                Key.REST_ARGS: {
                    **publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.definition,
                    'compress_settings': process_client.CompressTypeDef(
                        inner_directory='/sample_tif_colortable_nodata_opaque/',
                    ),
                },
                Key.EXP_INFO: {
                    **publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.info_values,
                    'file_extension': 'zip/sample_tif_colortable_nodata_opaque/sample_tif_colortable_nodata_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                },
                Key.EXP_THUMBNAIL: publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.thumbnail,
            },
            {
                Key.ACTION_NAME: 'patch-tif-colortable-to-natural-earth-vector-diacritics',
                Key.REST_ARGS: {
                    **publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND.definition,
                    'compress_settings': process_client.CompressTypeDef(
                        archive_name='ne_110m_admin_0_boundary lines land +ěščřžýáí',
                        inner_directory='/ne_110m_admin_0_boundary lines land +ěščřžýáí/',
                        file_name='ne_110m_admin_0_boundary_lines_land ížě',
                    ),
                },
                Key.EXP_INFO: {
                    **publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND.info_values,
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
                    'gdal_prefix': '/vsizip/',
                },
                Key.EXP_THUMBNAIL: publications.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND.thumbnail,
            },
            {
                Key.ACTION_NAME: 'patch-natural-earth-vector-to-tif-colortable',
                Key.REST_ARGS: {
                    **publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.definition,
                    'compress_settings': process_client.CompressTypeDef(
                        inner_directory='/sample_tif_colortable_nodata_opaque/',
                    ),
                },
                Key.EXP_INFO: {
                    **publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.info_values,
                    'file_extension': 'zip/sample_tif_colortable_nodata_opaque/sample_tif_colortable_nodata_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                },
                Key.EXP_THUMBNAIL: publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.thumbnail,
            },
        ]
    },
    'tif_type_change': {
        Key.RUN_ONLY_CASES: frozenset([WithChunksDomain, CompressDomain.TRUE]),
        Key.MANDATORY_CASES: frozenset([WithChunksDomain.TRUE, CompressDomain.TRUE]),
        Key.ACTIONS: [
            {
                Key.ACTION_NAME: 'post-tif-rgba',
                Key.REST_ARGS: {
                    **publications.SAMPLE_TIF_TFW_RGBA_OPAQUE.definition,
                },
                Key.EXP_INFO: {
                    **publications.SAMPLE_TIF_TFW_RGBA_OPAQUE.info_values,
                    'file_extension': 'zip/sample_tif_tfw_rgba_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                },
                Key.EXP_THUMBNAIL: publications.SAMPLE_TIF_TFW_RGBA_OPAQUE.thumbnail,
            },
            {
                Key.ACTION_NAME: 'patch-tif-rgba-to-tif-colortable',
                Key.REST_ARGS: {
                    **publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.definition,
                },
                Key.EXP_INFO: {
                    **publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.info_values,
                    'file_extension': 'zip/sample_tif_colortable_nodata_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                },
                Key.EXP_THUMBNAIL: publications.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.thumbnail,
            },
            {
                Key.ACTION_NAME: 'patch-tif-colortable-to-tif-rgba',
                Key.REST_ARGS: {
                    **publications.SAMPLE_TIF_TFW_RGBA_OPAQUE.definition,
                },
                Key.EXP_INFO: {
                    **publications.SAMPLE_TIF_TFW_RGBA_OPAQUE.info_values,
                    'file_extension': 'zip/sample_tif_tfw_rgba_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                },
                Key.EXP_THUMBNAIL: publications.SAMPLE_TIF_TFW_RGBA_OPAQUE.thumbnail,
            },
        ],
    },
}


def generate_test_cases():
    tc_list = []
    for key, test_case_params in TESTCASES.items():
        all_params = deepcopy(test_case_params)

        mandatory_cases = all_params.pop(Key.MANDATORY_CASES)
        specific_types = {mandatory_cases: EnumTestTypes.MANDATORY} if mandatory_cases else {}

        run_only_cases = case_to_simple_parametrizations(all_params.pop(Key.RUN_ONLY_CASES))
        all_cases = case_to_simple_parametrizations(ALL_CASES)
        ignore_cases = all_cases.difference(run_only_cases)
        for case in ignore_cases:
            assert case not in specific_types, f'key={key},\ncase={case},\nspecific_types={specific_types}'
            specific_types[case] = EnumTestTypes.IGNORE

        test_case = base_test.TestCaseType(key=key,
                                           type=EnumTestTypes.OPTIONAL,
                                           specific_types=specific_types,
                                           params=all_params,
                                           specific_params={},
                                           marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                           if test_case_params.get('xfail') else []
                                           )
        tc_list.append(test_case)
    return tc_list


@pytest.mark.timeout(600)
class TestLayer(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    test_cases = generate_test_cases()
    publication_type = process_client.LAYER_TYPE
    rest_parametrization = [
        WithChunksDomain,
        CompressDomain,
    ]

    def test_layer(self, layer: Publication4Test, rest_args: dict, params):
        for action_idx, action_def in enumerate(params[Key.ACTIONS]):
            print(f"Starting action idx={action_idx} name={action_def[Key.ACTION_NAME]}")

            assert not set(rest_args.keys()) & set(action_def[Key.REST_ARGS].keys())
            action_rest_args = {
                **rest_args,
                **action_def[Key.REST_ARGS],
            }
            rest_method_fn = self.post_publication if action_idx == 0 else self.patch_publication
            rest_method_fn(layer, action_rest_args)

            assert_util.is_publication_valid_and_complete(layer)
            asserts_publ.internal.correct_values_in_detail(*layer, **action_def[Key.EXP_INFO])
            asserts_publ.internal.thumbnail_equals(*layer, exp_thumbnail=action_def[Key.EXP_THUMBNAIL])
