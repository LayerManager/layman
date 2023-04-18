from copy import deepcopy
from contextlib import nullcontext as does_not_raise
from enum import Enum, unique
import os
import logging
import pytest

from layman import LaymanError
from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts import processing
from tests.asserts.final import publication as publication_asserts
from tests.asserts.final.publication import util as assert_utils
from tests.dynamic_data import base_test


@unique
class Key(Enum):
    REST_ARGS = 'rest_args'
    PUBLICATION_TYPE = 'publication_type'
    EXCEPTION = 'exception'
    EXPECTED_EXCEPTION = 'expected_exception'
    FAILED_INFO_KEY = 'failed_info_key'
    MANDATORY_CASES = 'mandatory_cases'
    IGNORED_CASES = 'ignored_cases'
    SPECIFIC_CASES = 'specific_params'


@unique
class ParametrizationSets(Enum):
    SIMPLE_POST_PATCH = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
    ])
    POST_PATCH_NO_CHUNKS_COMPRESS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
    ])
    POST_PATCH_CHUNKS_COMPRESS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])


DIRECTORY = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)

pytest_generate_tests = base_test.pytest_generate_tests


TESTCASES = {
    'shp_without_dbf': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.README.html',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 18,
            'message': 'Missing one or more ShapeFile files.',
            'data': {'missing_extensions': ['.dbf', '.prj'],
                     'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                     'path': 'ne_110m_admin_0_boundary_lines_land.shp',
                     },
        },
        Key.MANDATORY_CASES: ParametrizationSets.SIMPLE_POST_PATCH.value,
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_NO_CHUNKS_COMPRESS.value: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'},
                },
            },
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS.value: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'path': '{publication_name}.zip/ne_110m_admin_0_boundary_lines_land.shp'},
                    'sync': False,
                },
            },
        },
    },
}


def generate_test_cases():
    tc_list = []
    for key, test_case_params in TESTCASES.items():
        all_params = deepcopy(test_case_params)
        rest_args = all_params.pop(Key.REST_ARGS)
        specific_types = {tc: EnumTestTypes.MANDATORY for tc in all_params.pop(Key.MANDATORY_CASES)}
        for case in all_params.pop(Key.IGNORED_CASES, {}):
            assert case not in specific_types
            specific_types[case] = EnumTestTypes.IGNORE
        specific_params_def = all_params.pop(Key.SPECIFIC_CASES)
        specific_params = {}
        for parametrization_key, parametrization_value in specific_params_def.items():
            if all(isinstance(parametrization_item, frozenset) for parametrization_item in parametrization_key):
                for parametrization_item in parametrization_key:
                    specific_params[parametrization_item] = parametrization_value
            else:
                specific_params[parametrization_key] = parametrization_value
        publ_type = all_params.pop(Key.PUBLICATION_TYPE)
        test_case = base_test.TestCaseType(key=key,
                                           publication_type=publ_type,
                                           type=EnumTestTypes.OPTIONAL,
                                           specific_types=specific_types,
                                           rest_args=rest_args,
                                           params=all_params,
                                           specific_params=specific_params,
                                           marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                           if test_case_params.get('xfail') else []
                                           )
        tc_list.append(test_case)
    return tc_list


def format_exception(exception_info: dict, format_variables: dict):
    exception_info['data']['path'] = exception_info['data']['path'].format(**format_variables)


@pytest.mark.usefixtures('ensure_external_db')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = 'dynamic_test_workspace_wrong_input'
    test_cases = generate_test_cases()
    publication_type = None
    rest_parametrization = [
        base_test.RestMethod,
        base_test.WithChunksDomain,
        base_test.CompressDomain,
    ]

    def test_publication(self, publication: Publication, rest_method, rest_args, params):
        """Parametrized using pytest_generate_tests"""

        exp_exception = params[Key.EXPECTED_EXCEPTION]
        is_sync = exp_exception.pop('sync')
        format_exception(exp_exception, {'publication_name': publication.name})
        exception = pytest.raises(params[Key.EXCEPTION]) if is_sync else does_not_raise()
        with exception as exception_info:
            response = rest_method(publication, args=rest_args)
        if is_sync:
            processing.exception.response_exception(expected=exp_exception, thrown=exception_info)
            if rest_method == self.patch_publication:  # pylint: disable=W0143
                assert_utils.is_publication_valid_and_complete(publication)
        else:
            processing.response.valid_post(workspace=publication.workspace,
                                           publ_type=publication.type,
                                           name=publication.name,
                                           response=response,
                                           )
            rest_publication_detail = process_client.get_workspace_publication(publication_type=publication.type,
                                                                               workspace=publication.workspace,
                                                                               name=publication.name,
                                                                               )
            failed_info_key = params[Key.FAILED_INFO_KEY]
            publication_asserts.rest.async_error_in_info_key(rest_publication_detail=rest_publication_detail,
                                                             info_key=failed_info_key,
                                                             expected=exp_exception,
                                                             )
