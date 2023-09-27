import os

from layman import app
from layman.util import get_publication_info
from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test, base_test_classes


DIRECTORY = os.path.dirname(os.path.abspath(__file__))


WORKSPACE = 'test_map_json_workspace'
LAYER_HRANICE = Publication(WORKSPACE, process_client.LAYER_TYPE, 'hranice')


TEST_CASES = {
    'v2_0_0': {
        'file_path': os.path.join(DIRECTORY, '2_0_0_external_wms_internal_wms_internal_wfs.json'),
    },
    'v3_0_0': {
        'file_path': os.path.join(DIRECTORY, '3_0_0_external_wms_internal_wms_internal_wfs.json'),
    },
}

pytest_generate_tests = base_test.pytest_generate_tests


class TestPublication(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.MAP_TYPE

    rest_parametrization = [
        base_test_classes.RestMethod
    ]

    test_cases = [base_test.TestCaseType(key=key,
                                         type=EnumTestTypes.OPTIONAL,
                                         rest_args={
                                             'file_paths': [params['file_path']]
                                         },
                                         specific_types={
                                             (base_test_classes.RestMethod.POST, ): EnumTestTypes.MANDATORY
                                         }
                                         ) for key, params in TEST_CASES.items()]

    def before_class(self):
        self.post_publication(LAYER_HRANICE, args={
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.prj',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
            ],
        }, scope='class')


    def test_publication(self, map, rest_method, rest_args):
        rest_method.fn(map, args=rest_args)
        assert_util.is_publication_valid_and_complete(map)

        with app.app_context():
            publ_info = get_publication_info(map.workspace, map.type, map.name,
                                             context={'keys': ['map_layers']})

        assert publ_info['_map_layers'] == [
            {'index': 1,
             'name': 'hranice',
             'uuid': self.publ_uuids[LAYER_HRANICE],
             'workspace': self.workspace},
            {'index': 2,
             'name': 'mista',
             'uuid': None,
             'workspace': self.workspace},
        ]

        exp_thumbnail = os.path.join(DIRECTORY, 'exp_thumbnail.png')
        asserts_publ.internal.thumbnail_equals(map.workspace, map.type, map.name, exp_thumbnail,
                                               max_diffs=0)
