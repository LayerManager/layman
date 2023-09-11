import os
from layman import app
from layman.common import REQUEST_METHOD_POST
from layman.util import get_publication_info
from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test, base_test_classes

pytest_generate_tests = base_test.pytest_generate_tests


DIRECTORY = os.path.dirname(os.path.abspath(__file__))

TEST_CASES = {
    'post': {
        'rest_method': base_test_classes.RestMethodAll.POST,
        'rest_args': {
            'file_paths': [os.path.join(DIRECTORY, 'internal_wms_and_wfs.json')],
        },
        'post_before_test_args': {},
        'exp_before_rest_method': {
            'map_layers': None,
            'operates_on': None,
        },
        'exp_after_rest_method': {
            'map_layers': {
                # workspace, layer name, layer index, exists?
                ('layer_map_relation_workspace', 'hranice', 1, True),
                ('layer_map_relation_workspace', 'mista', 2, False),
                ('layer_map_relation_workspace', 'hranice', 3, True),
            },
            'operates_on': ['hranice'],
        },
    },
    'delete': {
        'rest_method': base_test_classes.RestMethodAll.DELETE,
        'rest_args': {},
        'post_before_test_args': {
            'file_paths': [os.path.join(DIRECTORY, 'internal_wms_and_wfs.json')],
        },
        'exp_before_rest_method': {
            'map_layers': {
                ('layer_map_relation_workspace', 'hranice', 1, True),
                ('layer_map_relation_workspace', 'mista', 2, False),
                ('layer_map_relation_workspace', 'hranice', 3, True),
            },
            'operates_on': ['hranice'],
        },
        'exp_after_rest_method': {
            'map_layers': None,
            'operates_on': None,
        },
    },
}


class TestPublication(base_test.TestSingleRestPublication):
    workspace = 'layer_map_relation_workspace'
    publication_type = process_client.MAP_TYPE

    rest_parametrization = []

    test_cases = [base_test.TestCaseType(key=key,
                                         params=params,
                                         rest_args=params['rest_args'],
                                         rest_method=params['rest_method'],
                                         post_before_test_args=params['post_before_test_args'],
                                         type=EnumTestTypes.MANDATORY,
                                         ) for key, params in TEST_CASES.items()]

    layer_uuids = {}

    def before_class(self):
        layer_name = 'hranice'
        resp = self.post_publication(Publication(self.workspace, process_client.LAYER_TYPE, layer_name), args={
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.prj',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
            ],
        }, scope='class')
        self.layer_uuids[layer_name] = resp['uuid']

    def assert_exp_map_layers(self, map, publ_info, exp_map_layers, exp_operates_on):
        if exp_map_layers is None:
            assert not publ_info
            assert exp_operates_on is None
        else:
            found_map_layers = {
                (ml['workspace'], ml['name'], ml['index'], ml['uuid'])
                for ml in publ_info['_map_layers']
            }
            exp_map_layers = {
                layer[:3] + ((self.layer_uuids[layer[1]] if layer[3] else None),)
                for layer in exp_map_layers
            }
            assert found_map_layers == exp_map_layers

            exp_operates_on = [
                {
                    "xlink:href": f"http://localhost:3080/csw?SERVICE=CSW&VERSION=2.0.2&REQUEST=GetRecordById&OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&ID=m-{self.layer_uuids[layer_name]}#_m-{self.layer_uuids[layer_name]}",
                    "xlink:title": layer_name,
                }
                for layer_name in exp_operates_on
            ]
            asserts_publ.metadata.correct_values_in_metadata(
                map.workspace, map.type, map.name, http_method=REQUEST_METHOD_POST, exp_values={
                    'operates_on': exp_operates_on,
                })

    def test_publication(self, map, rest_method, rest_args, params):
        with app.app_context():
            publ_info = get_publication_info(map.workspace, map.type, map.name,
                                             context={'keys': ['map_layers']})
        self.assert_exp_map_layers(map, publ_info, params['exp_before_rest_method']['map_layers'],
                                   params['exp_before_rest_method']['operates_on'])

        rest_method(map, args=rest_args)
        if rest_method == self.post_publication:  # pylint: disable=W0143
            assert_util.is_publication_valid_and_complete(map)

        with app.app_context():
            publ_info = get_publication_info(map.workspace, map.type, map.name,
                                             context={'keys': ['map_layers']})
        self.assert_exp_map_layers(map, publ_info, params['exp_after_rest_method']['map_layers'],
                                   params['exp_after_rest_method']['operates_on'])
