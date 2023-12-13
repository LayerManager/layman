import os
import pytest

from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as assert_util, internal as assert_internal
from tests.dynamic_data import base_test, base_test_classes

pytest_generate_tests = base_test.pytest_generate_tests

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

USER = 'test_patch_after_feature_change_role_user'
WORKSPACE = 'test_patch_after_feature_change_role_ws'  # public workspace
ROLE = 'TEST_PATCH_AFTER_FEATURE_CHANGE_ROLE_ROLE'
LAYER_SMALL = Publication(WORKSPACE, process_client.LAYER_TYPE, 'small_layer')
MAP = Publication(WORKSPACE, process_client.MAP_TYPE, 'map_hranice')


@pytest.mark.timeout(60)
@pytest.mark.usefixtures('oauth2_provider_mock')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = 'test_patch_after_feature_change_role'
    publication_type = process_client.LAYER_TYPE

    rest_parametrization = []

    usernames_to_reserve = [USER]

    test_cases = [base_test.TestCaseType(key='main',
                                         publication=Publication(WORKSPACE, process_client.LAYER_TYPE, LAYER_SMALL.name),
                                         rest_method=base_test_classes.RestMethod.PATCH,
                                         rest_args={
                                             'file_paths': [
                                                 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                                                 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
                                                 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.prj',
                                                 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                                                 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
                                             ],
                                             'actor_name': USER,
                                         },
                                         post_before_test_args={
                                             'actor_name': USER,
                                             'access_rights': {
                                                 'read': 'EVERYONE',
                                             },
                                         },
                                         type=EnumTestTypes.MANDATORY,
                                         marks=[pytest.mark.xfail(reason="Not fixed yet")]
                                         )]

    def before_class(self):
        self.post_publication(MAP, args={
            'file_paths': [os.path.join(DIRECTORY, 'patch_after_feature_change_map.json')],
            'access_rights': {
                'read': 'EVERYONE',
                'write': f'{ROLE},{USER}',
            },
            'actor_name': USER,
        }, scope='class')

    def test_publication(self, layer, rest_method, rest_args):
        # some initial asserts
        map_info = process_client.get_workspace_publication(MAP.type, MAP.workspace, MAP.name)
        assert map_info['access_rights']['write'] == [ROLE, USER]
        exp_thumbnail = os.path.join(DIRECTORY, f"patch_after_feature_change_map_empty.png")
        assert_internal.thumbnail_equals(MAP.workspace, MAP.type, MAP.name, exp_thumbnail, max_diffs=0)

        # send patch to layer to start patch_after_feature_change on MAP
        rest_method.fn(layer, args=rest_args)
        assert_util.is_publication_valid_and_complete(layer)

        # just ensure that patch_after_feature_change on MAP is running
        map_info = process_client.get_workspace_publication(MAP.type, MAP.workspace, MAP.name)
        assert map_info['layman_metadata']['publication_status'] == 'UPDATING'

        process_client.wait_for_publication_status(*MAP)

        # ensure that MAP thumbnail is OK, however MAP is OK even if thumbnail task failed !
        assert_util.is_publication_valid_and_complete(layer)

        # ensure that MAP thumbnail was updated
        exp_thumbnail = os.path.join(DIRECTORY, f"patch_after_feature_change_map_hranice.png")
        assert_internal.thumbnail_equals(MAP.workspace, MAP.type, MAP.name, exp_thumbnail, max_diffs=0)
