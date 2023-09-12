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

WORKSPACE = 'layer_map_relation_workspace'

LAYER_HRANICE = Publication(WORKSPACE, process_client.LAYER_TYPE, 'hranice')

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
                (WORKSPACE, 'hranice', 1, True),
                (WORKSPACE, 'mista', 2, False),
                (WORKSPACE, 'hranice', 3, True),
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
                (WORKSPACE, 'hranice', 1, True),
                (WORKSPACE, 'mista', 2, False),
                (WORKSPACE, 'hranice', 3, True),
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
    workspace = WORKSPACE
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
        resp = self.post_publication(LAYER_HRANICE, args={
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.prj',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
            ],
        }, scope='class')
        self.layer_uuids[LAYER_HRANICE.name] = resp['uuid']

    def assert_exp_map_layers(self, map, exp_map_layers, exp_operates_on):
        with app.app_context():
            publ_info = get_publication_info(map.workspace, map.type, map.name,
                                             context={'keys': ['map_layers']})
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

    @staticmethod
    def assert_exp_layer_maps(layer, map_operates_on_tuples):
        exp_layer_maps = sorted([
            (map.workspace, map.name)
            for map, operates_on in map_operates_on_tuples
            if layer.name in operates_on
        ])
        with app.app_context():
            found_layer_maps = [
                (m['workspace'], m['name'])
                for m in get_publication_info(*layer, context={'keys': ['layer_maps']})['_layer_maps']
            ]
        assert found_layer_maps == exp_layer_maps

    def test_publication(self, map, rest_method, rest_args, params):
        exp = params['exp_before_rest_method']
        self.assert_exp_map_layers(map, exp['map_layers'], exp['operates_on'])
        self.assert_exp_layer_maps(LAYER_HRANICE, [(map, exp['operates_on'] or [])])

        rest_method(map, args=rest_args)
        if rest_method == self.post_publication:  # pylint: disable=W0143
            assert_util.is_publication_valid_and_complete(map)

        exp = params['exp_after_rest_method']
        self.assert_exp_map_layers(map, exp['map_layers'], exp['operates_on'])
        self.assert_exp_layer_maps(LAYER_HRANICE, [(map, exp['operates_on'] or [])])
