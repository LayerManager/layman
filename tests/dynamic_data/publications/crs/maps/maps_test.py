import os
import pytest
import crs as crs_def
import tests
from layman import util as layman_util, names
from test_tools import process_client
from tests.asserts.final import publication as asserts_publ
from tests.dynamic_data import base_test
from ..... import Publication

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = 'dynamic_test_workspace_crs_maps'
LAYER_FOR_MAPS = Publication(WORKSPACE, process_client.LAYER_TYPE, "layer_for_map_crs")

KEY_INFO_VALUES = 'info_values'
KEY_THUMBNAIL_TOLERANCE = 'thumbnail_tolerance'

TEST_CASES = {
    crs_def.EPSG_4326: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [14.114369, 48.964832, 14.126823999999997, 48.970612],
                'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.8542061958, 6269876.335616991],
            }
        },
        KEY_THUMBNAIL_TOLERANCE: 5,
    },
    crs_def.EPSG_3857: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [1571204.369948366, 6268896.225570714, 1572590.8542061956, 6269876.335616991],
                'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.8542061956, 6269876.335616991],
            }
        },
        KEY_THUMBNAIL_TOLERANCE: 5,
    },
    crs_def.EPSG_5514: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [-782334.8391616135, -1164023.7276125506, -780840.5943329989, -1162648.8238845991],
                'bounding_box': [1570625.93383904, 6268188.730239409, 1573168.3505425507, 6270583.885785243],
            }
        },
        KEY_THUMBNAIL_TOLERANCE: 318,
    },
}

pytest_generate_tests = base_test.pytest_generate_tests


@pytest.mark.xfail(reason='Map filesystem input_file in not yet ready for WMS layers named by UUID')
class TestMap(base_test.TestSingleRestPublication):

    workspace = WORKSPACE

    publication_type = process_client.MAP_TYPE

    rest_parametrization = [
        base_test.RestMethod,
    ]

    test_cases = [base_test.TestCaseType(key=key,
                                         params=params,
                                         type=tests.EnumTestTypes.MANDATORY,
                                         ) for key, params in TEST_CASES.items()]

    def before_class(self):
        self.post_publication(LAYER_FOR_MAPS, scope='class')

    def test_input_crs(self, map, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        map_crs = key
        uuid = layman_util.get_publication_uuid(LAYER_FOR_MAPS.workspace, process_client.LAYER_TYPE, LAYER_FOR_MAPS.name)
        gs_wms_layername = names.get_layer_names_by_source(uuid=uuid).wms.name
        map_args = {
            'map_layers': [(LAYER_FOR_MAPS.workspace, gs_wms_layername)],
            'native_extent': params[KEY_INFO_VALUES]['exp_publication_detail']['native_bounding_box'],
            'crs': map_crs,
            'title': map.name,
        }
        rest_method.fn(map, args=map_args)

        exp_publication_detail = {
            'description': 'Map generated for internal layers',
            'native_crs': map_crs,
            'title': map.name,
            '_map_layers': [{
                'name': LAYER_FOR_MAPS.name,
                'workspace': LAYER_FOR_MAPS.workspace,
                'index': 1,
                'uuid': self.publ_uuids[LAYER_FOR_MAPS],
            }],
            **params.get(KEY_INFO_VALUES, {}).get('exp_publication_detail', {})
        }
        asserts_publ.internal.correct_values_in_detail(map.workspace, map.type, map.name,
                                                       exp_publication_detail=exp_publication_detail,
                                                       )
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_{map_crs.replace(':', '_').lower()}.png")
        asserts_publ.internal.thumbnail_equals(map.workspace, map.type, map.name, exp_thumbnail, max_diffs=params[KEY_THUMBNAIL_TOLERANCE])
