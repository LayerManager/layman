import pytest

from geoserver.error import Error as GsError
from layman import LaymanError
from test_tools.data import wfs as wfs_data
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
class TestReadOnlyTable(base_test.TestSingleRestPublication):

    workspace = 'wrong_input_wfst_read_only_ws'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(key=key,
                                         type=EnumTestTypes.MANDATORY,
                                         rest_args={
                                             'db_connection': f"{external_db.READ_ONLY_URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE}&geo_column=wkb_geometry",
                                         }
                                         ) for key, params in TEST_CASES.items()]

    def before_class(self):
        self.import_external_table(INPUT_FILE_PATH, {
            'schema': EXTERNAL_DB_SCHEMA,
            'table': EXTERNAL_DB_TABLE,
        }, scope='class')

    def test_proxy_raises(self, layer: Publication, rest_args):
        self.ensure_publication(layer, args=rest_args)

        # data in read-only table can not be changed by WFS-T
        data_xml = wfs_data.get_wfs20_insert_points(layer.workspace, layer.name)
        with pytest.raises(GsError) as exc_info:
            process_client.post_wfst(data_xml, workspace=layer.workspace)
        assert exc_info.value.message == 'WFS-T error'
        assert exc_info.value.data == {'status_code': 500}

        assert_publ_util.is_publication_valid_and_complete(layer)

        # new attributes can not be added to read-only table
        data_xml = wfs_data.get_wfs20_insert_points_new_attr(layer.workspace, layer.name, ['new_attr'])
        with pytest.raises(LaymanError) as exc_info:
            process_client.post_wfst(data_xml, workspace=layer.workspace)
        assert exc_info.value.http_code == 403
        assert exc_info.value.code == 7
        assert exc_info.value.message == 'Database query error'
        assert exc_info.value.data == {'reason': 'Insufficient privilege'}

        assert_publ_util.is_publication_valid_and_complete(layer)
