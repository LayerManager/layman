from copy import deepcopy
import os
import pytest

import crs as crs_def
from layman import common, app
from layman.layer.layer_class import Layer
from test_tools import process_client
from tests import EnumTestTypes, Publication4Test, EnumTestKeys
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as asserts_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

LAYERS = {
    'one_file_format_simple': {
        'rest_args': {
            'time_regex': r'^.*([0-9]{4})([0-9]{2})([0-9]{2}).*$',
            'time_regex_format': 'yyyyddMM',
            'with_chunks': True,
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20221603.tif'),
            ],
        },
        'do_complex_test': False,
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737176.364826313, 6500364.015801598, 1751338.4804418762, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5573500.0, 552100.0, 5579500.0],
                'image_mosaic': True,
                'wms': {
                    'time': {'default': '2022-03-16T00:00:00.000Z',
                             'units': 'ISO8601',
                             'regex': '^.*([0-9]{4})([0-9]{2})([0-9]{2}).*$',
                             'regex_format': 'yyyyddMM',
                             'values': ['2022-03-16T00:00:00.000Z']},
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'filenames': [
                'S2A_MSIL2A_20221603.tif',
            ],
        },
    },
}


def generate_test_cases():
    tc_list = []
    for name, test_case_params in LAYERS.items():
        all_params = deepcopy(test_case_params)
        rest_args = all_params.pop('rest_args')
        test_case = base_test.TestCaseType(key=name,
                                           type=test_case_params.get(EnumTestKeys.TYPE, EnumTestTypes.MANDATORY),
                                           rest_args=rest_args,
                                           params=all_params,
                                           marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                           if test_case_params.get('xfail') else []
                                           )
        tc_list.append(test_case)
    return tc_list


class TestLayer(base_test.TestSingleRestPublication):
    workspace = 'dynamic_test_workspace_timeseries_layer'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
        # base_test.RestMethod,
        # base_test.RestArgs.WITH_CHUNKS,
    ]

    test_cases = generate_test_cases()

    @pytest.mark.timeout(60)
    @pytest.mark.repeat(10)
    def test_timeseries_layer(self, layer: Publication4Test, params, rest_method, rest_args):
        """Parametrized using pytest_generate_tests"""
        rest_method.fn(layer, args=rest_args)

        asserts_util.is_publication_valid_and_complete(layer)

        asserts_publ.internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                       **params.get('detail_values', {}),
                                                       )

        if params['do_complex_test']:
            with app.app_context():
                prod_layer = Layer(uuid=self.publ_uuids[layer])
            time_snaps = [time_snap[:10] for time_snap in params['detail_values']['exp_publication_detail']['wms']['time']['values']]
            for time in time_snaps:
                exp_wms = os.path.join(DIRECTORY, f"wms_{time}.png")
                asserts_publ.geoserver.wms_spatial_precision(layer.workspace, layer.type, layer.name, crs=crs_def.EPSG_3857,
                                                             extent=params['wms_bbox'],
                                                             img_size=(1322, 554),
                                                             wms_version='1.3.0',
                                                             pixel_diff_limit=200,
                                                             obtained_file_path=f'tmp/artifacts/test_timeseries/downloaded_wms_{layer.name}_{time}.png',
                                                             expected_file_path=exp_wms,
                                                             time=time,
                                                             )

            exp_thumbnail_file = params.get('expected_thumbnail')
            if exp_thumbnail_file is not None:
                exp_thumbnail = os.path.join(DIRECTORY, exp_thumbnail_file)
                asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)

            if rest_method.enum_item == base_test.RestMethod.POST:
                http_method = common.REQUEST_METHOD_POST
            elif rest_method.enum_item == base_test.RestMethod.PATCH:
                http_method = common.REQUEST_METHOD_PATCH
            else:
                raise NotImplementedError(f"Unknown rest_method: {rest_method}")

            asserts_publ.metadata.correct_values_in_metadata(prod_layer, http_method=http_method)

            process_client.patch_workspace_layer(layer.workspace,
                                                 layer.name,
                                                 title='Title: ' + layer.name)
            asserts_util.is_publication_valid_and_complete(layer)

            process_client.patch_workspace_layer(layer.workspace,
                                                 layer.name,
                                                 file_paths=['sample/layman.layer/small_layer.geojson'],
                                                 title=layer.name)
            asserts_util.is_publication_valid_and_complete(layer)

            asserts_publ.internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                           exp_publication_detail={
                                                               'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196,
                                                                                6269876.335616991],
                                                               'native_crs': 'EPSG:4326',
                                                               'native_bounding_box': [14.114369, 48.964832, 14.126824, 48.970612],
                                                           },
                                                           file_extension='geojson',
                                                           publ_type_detail=('vector', 'sld'),
                                                           )
