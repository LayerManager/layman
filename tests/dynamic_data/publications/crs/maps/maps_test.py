import crs as crs_def
from test_tools import process_client
import tests.asserts.final.publication as asserts_publ
from tests.dynamic_data import base_test
from ..... import Publication


LAYER_FOR_MAPS = "layer_for_map_crs"

KEY_INFO_VALUES = 'info_values'
KEY_DEFINITION = base_test.KEY_DEFINITION

TEST_CASES = {
    crs_def.EPSG_4326: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [14.114369, 48.964832, 14.126823999999997, 48.970612],
                'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.8542061958, 6269876.335616991],
            }
        },
    },
    crs_def.EPSG_3857: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [1571204.369948366, 6268896.225570714, 1572590.8542061956, 6269876.335616991],
                'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.8542061956, 6269876.335616991],
            }
        },
    },
    crs_def.EPSG_5514: {
        KEY_DEFINITION: {
            'native_extent': [-782190.2850904732, -1163856.3670231388, -780984.9048069374, -1162816.2134994941],
        },
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [-782334.8391616135, -1164023.7276125506, -780840.5943329989, -1162648.8238845991],
                'bounding_box': [1570625.93383904, 6268188.730239409, 1573168.3505425507, 6270583.885785243],
            }
        },
    },
}

pytest_generate_tests = base_test.pytest_generate_tests


class TestMap(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_crs_maps'

    publication_type = process_client.MAP_TYPE

    test_cases = TEST_CASES

    def before_class(self):
        self.post_publication(Publication(self.workspace, process_client.LAYER_TYPE, LAYER_FOR_MAPS), scope='class')

    def test_input_crs(self, publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        map = publication
        map_crs = key
        layer_name = LAYER_FOR_MAPS
        map_params = {
            'map_layers': [(self.workspace, layer_name)],
            'native_extent': params[KEY_INFO_VALUES]['exp_publication_detail']['native_bounding_box'],
            'crs': map_crs,
            'title': publication.name,
            **params.get(KEY_DEFINITION, {}),
        }
        rest_method(map, params=map_params)

        exp_publication_detail = {
            'description': 'Map generated for internal layers',
            'native_crs': map_crs,
            'title': publication.name,
            **params.get(KEY_INFO_VALUES, {}).get('exp_publication_detail', {})
        }
        asserts_publ.internal.correct_values_in_detail(map.workspace, map.type, map.name,
                                                       exp_publication_detail=exp_publication_detail,
                                                       )
