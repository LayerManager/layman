from copy import deepcopy
from enum import Enum, unique
import os
import pytest

from test_tools import process_client
from tests import EnumTestTypes, Publication4Test
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test
from tests.dynamic_data.base_test import RestMethod, WithChunksDomain, CompressDomain
from tests.dynamic_data.base_test_util import case_to_simple_parametrizations
from tests.dynamic_data.publications import common_publications

pytest_generate_tests = base_test.pytest_generate_tests
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = "test_edge_cases_ws"
ALL_CASES = frozenset([RestMethod, WithChunksDomain, CompressDomain])


@unique
class Key(Enum):
    REST_ARGS = 'rest_args'
    PUBLICATION_TYPE = 'publication_type'
    MANDATORY_CASES = 'mandatory_cases'
    RUN_ONLY_CASES = 'run_only_cases'
    WORKSPACE = 'workspace'
    EXP_INFO = 'exp_info'
    EXP_THUMBNAIL = 'exp_thumbnail'


TESTCASES = {
    'zip_and_other_than_main_file': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'sample/style/small_layer.qml',
                'sample/layman.layer/small_layer.zip',
            ],
        },
        Key.EXP_INFO: common_publications.SMALL_LAYER_ZIP.info_values,
        Key.EXP_THUMBNAIL: common_publications.SMALL_LAYER_ZIP.thumbnail,
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: frozenset([RestMethod, WithChunksDomain, CompressDomain.FALSE]),
    },
    'capslock_extension_zip': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'sample/layman.layer/smaLL_Layer.ZIP',
            ],
        },
        Key.EXP_INFO: common_publications.SMALL_LAYER_ZIP.info_values,
        Key.EXP_THUMBNAIL: common_publications.SMALL_LAYER_ZIP.thumbnail,
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: frozenset([RestMethod, WithChunksDomain, CompressDomain.FALSE]),
    },
    'capslock_extension_geojson': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'sample/layman.layer/SMAll_layER.GeOjSoN',
            ],
        },
        Key.EXP_INFO: None,
        Key.EXP_THUMBNAIL: common_publications.SMALL_LAYER.thumbnail,
        Key.MANDATORY_CASES: frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        Key.RUN_ONLY_CASES: frozenset([RestMethod, WithChunksDomain, CompressDomain]),
    },
    'capslock_extension_json': {
        Key.PUBLICATION_TYPE: process_client.MAP_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'sample/layman.map/smaLL_Map.jSOn',
            ],
        },
        Key.EXP_INFO: None,
        Key.EXP_THUMBNAIL: None,
        Key.MANDATORY_CASES: frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        Key.RUN_ONLY_CASES: frozenset([RestMethod, WithChunksDomain.FALSE, CompressDomain.FALSE]),
    },
    'invalid_byte_sequence': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                f'{DIRECTORY}/invalid_byte_sequence.zip',
            ],
            'crs': 'EPSG:5514',
        },
        Key.EXP_INFO: None,
        Key.EXP_THUMBNAIL: f'{DIRECTORY}/thumbnail_invalid_byte_sequence.png',
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: frozenset([RestMethod, WithChunksDomain, CompressDomain]),
    },
    'styled_raster_issue_681': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['/code/sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif'],
            'style_file': os.path.join(DIRECTORY, 'raster_float_grayscale_alpha_contrast_enhancement.sld'),
        },
        Key.EXP_INFO: None,
        Key.EXP_THUMBNAIL: f'{DIRECTORY}/thumbnail_styled_raster_issue_681.png',
        Key.MANDATORY_CASES: frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        Key.RUN_ONLY_CASES: frozenset([RestMethod, WithChunksDomain, CompressDomain]),
    },
}


def generate_test_cases():
    tc_list = []
    for key, test_case_params in TESTCASES.items():
        all_params = deepcopy(test_case_params)
        rest_args = all_params.pop(Key.REST_ARGS)

        mandatory_cases = all_params.pop(Key.MANDATORY_CASES)
        specific_types = {mandatory_cases: EnumTestTypes.MANDATORY} if mandatory_cases else {}

        run_only_cases = case_to_simple_parametrizations(all_params.pop(Key.RUN_ONLY_CASES))
        all_cases = case_to_simple_parametrizations(ALL_CASES)
        ignore_cases = all_cases.difference(run_only_cases)
        for case in ignore_cases:
            assert case not in specific_types, f'key={key},\ncase={case},\nspecific_types={specific_types}'
            specific_types[case] = EnumTestTypes.IGNORE

        publ_type = all_params.pop(Key.PUBLICATION_TYPE)

        publication = Publication4Test(workspace=WORKSPACE,
                                       type=publ_type,
                                       name=None,
                                       )

        test_case = base_test.TestCaseType(key=key,
                                           publication=publication,
                                           publication_type=publ_type,
                                           type=EnumTestTypes.OPTIONAL,
                                           specific_types=specific_types,
                                           rest_args=rest_args,
                                           params=all_params,
                                           specific_params={},
                                           marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                           if test_case_params.get('xfail') else []
                                           )
        tc_list.append(test_case)
    return tc_list


class TestPublication(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    test_cases = generate_test_cases()
    publication_type = None
    rest_parametrization = [
        RestMethod,
        WithChunksDomain,
        CompressDomain,
    ]

    def test_publication(self, publication: Publication4Test, rest_method, rest_args, params):
        rest_method.fn(publication, args=rest_args)
        assert_util.is_publication_valid_and_complete(publication)
        if params[Key.EXP_INFO] is not None:
            asserts_publ.internal.correct_values_in_detail(*publication,
                                                           **params[Key.EXP_INFO],
                                                           )
        if params[Key.EXP_THUMBNAIL] is not None:
            asserts_publ.internal.thumbnail_equals(*publication,
                                                   exp_thumbnail=params[Key.EXP_THUMBNAIL],
                                                   )
