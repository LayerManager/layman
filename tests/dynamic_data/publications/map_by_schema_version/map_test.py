import json
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
        'exp_map_file': os.path.join(DIRECTORY, 'exp_2_0_0_map_file.json'),
    },
    'v3_0_0': {
        'file_path': os.path.join(DIRECTORY, '3_0_0_external_wms_internal_wms_internal_wfs.json'),
        'exp_map_file': os.path.join(DIRECTORY, 'exp_3_0_0_map_file.json'),
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
                                         params=params,
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

    @staticmethod
    def assert_get_workspace_map_file(map, exp_file):
        headers = {'X-Forwarded-Proto': 'https',
                   'X-Forwarded-Host': 'enjoychallenge.tech',
                   'X-Forwarded-Prefix': '/new-client-proxy',
                   }

        resp = process_client.get_workspace_map_file(map.type, map.workspace, map.name, headers=headers)
        with open(exp_file, encoding='utf-8') as file:
            exp_json = json.load(file)
        exp_json['name'] = map.name
        exp_json['title'] = resp['title']
        assert resp == exp_json

    def test_publication(self, map, rest_method, rest_args, params):
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
        self.assert_get_workspace_map_file(map, params['exp_map_file'])
