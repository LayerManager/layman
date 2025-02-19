import copy
import pytest

from geoserver.error import Error as GsError
from layman import LaymanError, names
from test_tools import process_client, external_db
from test_tools.data import wfs as wfs_data
from test_tools.util import assert_error
from tests import Publication, EnumTestTypes
from tests.asserts.final.publication import util as assert_publ_util
from tests.dynamic_data import base_test, base_test_classes


INPUT_FILE_PATH = 'sample/layman.layer/small_layer.geojson'
EXTERNAL_DB_TABLE = 'small_layer'
EXTERNAL_DB_SCHEMA = 'public'

WORKSPACE = 'wrong_input_wfst_ws'
EDITABLE_TABLE_LAYER = base_test.Publication(WORKSPACE, process_client.LAYER_TYPE, 'editable_table_layer')
READ_ONLY_TABLE_LAYER = base_test.Publication(WORKSPACE, process_client.LAYER_TYPE, 'read_only_table_layer')

TEST_CASES = {
    'editable_table_dangerous_attribute_name': {
        'layer': EDITABLE_TABLE_LAYER,
        'wfst_data_method': wfs_data.get_wfs20_insert_points_new_attr,
        'wfst_data_args': ([
            'new_ok_attr',
            'new-dangerous-attr-with-dashes2',
            'new-dangerous-attr-with-dashes',
        ], ),
        'exp_exception': {
            'class': LaymanError,
            'code': 2,
            'http_code': 400,
            'data': {
                'expected': r'Attribute names matching regex ^[a-zA-Z_][a-zA-Z_0-9]*$',
                'found': ['new-dangerous-attr-with-dashes', 'new-dangerous-attr-with-dashes2'],
            }
        }
    },
    'read_only_table_dangerous_attribute_name': {
        'layer': READ_ONLY_TABLE_LAYER,
        'wfst_data_method': wfs_data.get_wfs20_insert_points_new_attr,
        'wfst_data_args': (['new_attr'], ),
        'exp_exception': {
            'class': LaymanError,
            'code': 7,
            'http_code': 403,
            'message': 'Database query error',
            'data': {'reason': 'Insufficient privilege'}
        }
    },
    'read_only_table_insert': {
        'layer': READ_ONLY_TABLE_LAYER,
        'wfst_data_method': wfs_data.get_wfs20_insert_points,
        'wfst_data_args': tuple(),
        'exp_exception': {
            'class': GsError,
            'message': 'WFS-T error',
            'data': {'status_code': 500}
        },
    },
}


pytest_generate_tests = base_test.pytest_generate_tests


@pytest.mark.usefixtures('ensure_external_db')
class TestWfst(base_test.TestSingleRestPublication):

    workspace = WORKSPACE

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(key=key,
                                         type=EnumTestTypes.OPTIONAL,
                                         publication=copy.deepcopy(params['layer']),
                                         params=params,
                                         ) for key, params in TEST_CASES.items()]

    external_tables_to_create = [base_test_classes.ExternalTableDef(file_path=INPUT_FILE_PATH,
                                                                    db_schema=EXTERNAL_DB_SCHEMA,
                                                                    db_table=EXTERNAL_DB_TABLE,),
                                 ]

    def before_class(self):
        self.post_publication(EDITABLE_TABLE_LAYER, args={
            'external_table_uri': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE}&geo_column=wkb_geometry",
        }, scope='class')
        self.post_publication(READ_ONLY_TABLE_LAYER, args={
            'external_table_uri': f"{external_db.READ_ONLY_URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE}&geo_column=wkb_geometry",
        }, scope='class')

    def test_proxy_raises(self, layer: Publication, params):
        layer_uuid = self.publ_uuids[layer]
        gs_layer_wfs = names.get_layer_names_by_source(uuid=layer_uuid, ).wfs
        data_xml = params['wfst_data_method'](gs_layer_wfs.workspace, gs_layer_wfs.name, *params['wfst_data_args'])

        exp_exception = params['exp_exception']
        exception_class = exp_exception.pop('class')
        with pytest.raises(exception_class) as exc_info:
            process_client.post_wfst(data_xml, workspace=gs_layer_wfs.workspace)

        assert_error(exp_exception, exc_info)

        assert_publ_util.is_publication_valid_and_complete(layer)
