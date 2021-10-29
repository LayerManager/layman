import copy

from layman import LaymanError
from tests.asserts import util as asserts_util
import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client
from ... import Action, Publication, dynamic_data as consts

KEY_PUBLICATION_TYPE = 'publ_type'
KEY_ACTION_PARAMS = 'action_params'
KEY_EXPECTED_EXCEPTION = 'expected_exception'
KEY_EXPECTED_EXCEPTION_ZIPPED = 'expected_exception_zipped'
KEY_EXPECTED_EXCEPTION_CHUNKS_ZIPPED = 'expected_exception_chunks_zipped'

TESTCASES = {
    'shp_without_dbf': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.README.html',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {'http_code': 400,
                                 'code': 18,
                                 'message': 'Missing one or more ShapeFile files.',
                                 'detail': {'missing_extensions': ['.dbf', '.prj'],
                                            'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                                            'path': 'ne_110m_admin_0_boundary_lines_land.shp',
                                            },
                                 },
        KEY_EXPECTED_EXCEPTION_ZIPPED: {'detail': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
        KEY_EXPECTED_EXCEPTION_CHUNKS_ZIPPED: {'detail': {'path': '/layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/shp_without_dbf_post_chunks_zipped/input_file/shp_without_dbf_post_chunks_zipped.zip/ne_110m_admin_0_boundary_lines_land.shp'}}
    },
}


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    result = dict()
    for testcase, tc_params in TESTCASES.items():
        post = [{
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                        tc_params[KEY_ACTION_PARAMS]),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': tc_params[KEY_EXPECTED_EXCEPTION], }, ),
                    ],
                }, },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        }]
        post_sync_zipped = [{
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                        {**tc_params[KEY_ACTION_PARAMS],
                                         'compress': True, }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception,
                               {'expected': asserts_util.recursive_dict_update(copy.deepcopy(tc_params[KEY_EXPECTED_EXCEPTION]),
                                                                               tc_params.get(
                                                                                   KEY_EXPECTED_EXCEPTION_ZIPPED, dict()), )}, ),
                    ],
                }, },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        }]
        post_chunks = [{
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                        {**tc_params[KEY_ACTION_PARAMS],
                                         'with_chunks': True, }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': tc_params[KEY_EXPECTED_EXCEPTION], }, ),
                    ],
                }, },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        }]
        post_chunks_zipped = [{
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                        {**tc_params[KEY_ACTION_PARAMS],
                                         'compress': True,
                                         'with_chunks': True, }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.rest.async_error_in_info_key, {'info_key': 'file',
                                                                  'expected': asserts_util.recursive_dict_update(
                                                                      copy.deepcopy(tc_params[KEY_EXPECTED_EXCEPTION]),
                                                                      tc_params.get(
                                                                          KEY_EXPECTED_EXCEPTION_CHUNKS_ZIPPED, dict()), ), }, ),
            ],
        }]
        result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], testcase + '_post_sync')] = post
        result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], testcase + '_post_sync_zipped')] = post_sync_zipped
        result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], testcase + '_post_chunks')] = post_chunks
        result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], testcase + '_post_chunks_zipped')] = post_chunks_zipped

    return result
