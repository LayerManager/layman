import os
from layman import app
from layman.util import get_publication_info
from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test, base_test_classes

pytest_generate_tests = base_test.pytest_generate_tests


DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class RestMethodLocal(base_test_classes.RestMethodBase):
    POST = ('post_publication', 'post')
    DELETE = ('delete_workspace_publication', 'delete')


TEST_CASES = {
    'post': {
        'rest_method': RestMethodLocal.POST,
        'rest_args': {
            'file_paths': [os.path.join(DIRECTORY, 'internal_wms_and_wfs.json')],
        },
        'post_before_test_args': {},
        'exp_map_layers_before_rest_method': None,
        'exp_map_layers_after_rest_method': {
            # workspace, layer name, layer index, exists?
            ('layer_map_relation_workspace', 'hranice', 1, True),
            ('layer_map_relation_workspace', 'mista', 2, False),
            ('layer_map_relation_workspace', 'hranice', 3, True),
        },
    },
    'delete': {
        'rest_method': RestMethodLocal.DELETE,
        'rest_args': {},
        'post_before_test_args': {
            'file_paths': [os.path.join(DIRECTORY, 'internal_wms_and_wfs.json')],
        },
        'exp_map_layers_before_rest_method': {
            ('layer_map_relation_workspace', 'hranice', 1, True),
            ('layer_map_relation_workspace', 'mista', 2, False),
            ('layer_map_relation_workspace', 'hranice', 3, True),
        },
        'exp_map_layers_after_rest_method': None,
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

    @classmethod
    def delete_workspace_publication(cls, publication, args=None):
        return process_client.delete_workspace_publication(publication.type, publication.workspace, publication.name, **args)

    def assert_exp_map_layers(self, publ_info, exp_map_layers):
        if exp_map_layers is None:
            assert not publ_info
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

    def test_publication(self, map, rest_method, rest_args, params, parametrization: base_test.Parametrization):
        with app.app_context():
            publ_info = get_publication_info(map.workspace, map.type, map.name,
                                             context={'keys': ['map_layers']})
        self.assert_exp_map_layers(publ_info, params['exp_map_layers_before_rest_method'])

        rest_method(map, args=rest_args)
        if parametrization.rest_method == RestMethodLocal.POST:
            assert_util.is_publication_valid_and_complete(map)

        with app.app_context():
            publ_info = get_publication_info(map.workspace, map.type, map.name,
                                             context={'keys': ['map_layers']})
        self.assert_exp_map_layers(publ_info, params['exp_map_layers_after_rest_method'])
