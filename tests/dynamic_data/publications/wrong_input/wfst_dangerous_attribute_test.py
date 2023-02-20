import pytest

from layman import LaymanError
from test_tools.data.wfs import get_wfs20_insert_points_new_attr
from test_tools import process_client, external_db
from tests import Publication, EnumTestTypes
from tests.asserts.final.publication import util as assert_publ_util
from tests.dynamic_data import base_test


INPUT_FILE_PATH = 'sample/layman.layer/small_layer.geojson'
EXTERNAL_DB_TABLE = 'small_layer'
EXTERNAL_DB_SCHEMA = 'public'


TEST_CASES = {
    'single': {},
}


pytest_generate_tests = base_test.pytest_generate_tests


@pytest.mark.usefixtures('ensure_external_db')
class TestDangerousAttribute(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_wfst_refresh'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(key=key,
                                         type=EnumTestTypes.MANDATORY,
                                         rest_args={
                                             'db_connection': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE}&geo_column=wkb_geometry",
                                         }
                                         ) for key, params in TEST_CASES.items()]

    def before_class(self):
        self.import_external_table(INPUT_FILE_PATH, {
            'schema': EXTERNAL_DB_SCHEMA,
            'table': EXTERNAL_DB_TABLE,
        }, scope='class')

    def test_proxy_raises(self, layer: Publication, rest_args):
        self.post_publication(layer, args=rest_args)

        data_xml = get_wfs20_insert_points_new_attr(layer.workspace, layer.name, [
            'new_ok_attr',
            'new-dangerous-attr-with-dashes2',
            'new-dangerous-attr-with-dashes',
        ])
        with pytest.raises(LaymanError) as exc_info:
            process_client.post_wfst(data_xml, workspace=layer.workspace)
        assert exc_info.value.code == 2
        assert exc_info.value.http_code == 400
        assert exc_info.value.data['expected'] == r'Attribute names matching regex ^[a-zA-Z_][a-zA-Z_0-9]*$'
        assert exc_info.value.data['found'] == ['new-dangerous-attr-with-dashes', 'new-dangerous-attr-with-dashes2']

        assert_publ_util.is_publication_valid_and_complete(layer)
