import os
from test_tools import process_client, assert_util
from test_tools.data import wfs as data_wfs, SMALL_LAYER_NATIVE_CRS, SMALL_LAYER_BBOX, SMALL_LAYER_NATIVE_BBOX
from tests import Publication, EnumTestTypes
from tests.asserts.final import publication as asserts_publ
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

LAYER_FOR_MAPS = "layer_for_map_crs"

KEY_INFO_VALUES = 'info_values'


class StyleFileDomain(base_test.StyleFileDomainBase):
    SLD = ((None, 'sld'), 'sld')
    QML = (('sample/style/small_layer.qml', 'qml'), 'qml')


TEST_CASES = {
    'internal_db': {},
}

pytest_generate_tests = base_test.pytest_generate_tests


class TestRefresh(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_crs_maps'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
        StyleFileDomain,
    ]

    test_cases = [base_test.TestCaseType(key=key,
                                         type=EnumTestTypes.MANDATORY,
                                         ) for key, params in TEST_CASES.items()]

    def test_refresh(self, layer: Publication, rest_args, parametrization: base_test.Parametrization):
        self.post_publication(layer, args=rest_args)
        thumbnail_style_postfix = parametrization.style_file.publ_name_part

        native_crs = SMALL_LAYER_NATIVE_CRS
        assert_util.assert_all_sources_bbox(layer.workspace, layer.name, SMALL_LAYER_BBOX,
                                            expected_native_bbox=SMALL_LAYER_NATIVE_BBOX,
                                            expected_native_crs=native_crs)

        expected_bbox = (1571000.0, 6268800.0, 1572590.854206196, 6269876.33561699)
        exp_native_bbox = (14.112533113517683, 48.964264493114904, 14.126824, 48.970612)
        wfst_actions = [
            (data_wfs.get_wfs20_insert_points, expected_bbox, exp_native_bbox, '_bigger'),
            (data_wfs.get_wfs20_delete_point, SMALL_LAYER_BBOX, SMALL_LAYER_NATIVE_BBOX, ''),
        ]

        for wfs_method, exp_bbox, exp_native_bbox, thumbnail_bbox_postfix in wfst_actions:
            data_xml = wfs_method(layer.workspace, layer.name, )
            process_client.post_wfst(data_xml, workspace=layer.workspace)
            process_client.wait_for_publication_status(layer.workspace, process_client.LAYER_TYPE, layer.name)

            assert_util.assert_all_sources_bbox(layer.workspace, layer.name, exp_bbox,
                                                expected_native_bbox=exp_native_bbox,
                                                expected_native_crs=native_crs)

            expected_thumbnail_path = f'/code/sample/style/test_wfs_bbox_layer_{thumbnail_style_postfix}{thumbnail_bbox_postfix}.png'
            asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, expected_thumbnail_path,
                                                   max_diffs=5)
