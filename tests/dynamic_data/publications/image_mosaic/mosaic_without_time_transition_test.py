import os

from layman import app, util as layman_util
from test_tools import process_client
from tests import Publication4Test
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

pytest_generate_tests = base_test.pytest_generate_tests

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = 'dynamic_test_workspace_mosaic_without_time'

MOSAIC_DATA_DIR = 'tests/dynamic_data/publications/image_mosaic/data'
MOSAIC_RASTER_1 = f'{MOSAIC_DATA_DIR}/1.tif'
MOSAIC_RASTER_2 = f'{MOSAIC_DATA_DIR}/2.tif'
TIMESERIES_DATA_DIR = 'tests/dynamic_data/publications/layer_timeseries/timeseries_tif'
TIMESERIES_RASTER_20220316 = f'{TIMESERIES_DATA_DIR}/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'
TIMESERIES_RASTER_20220319 = f'{TIMESERIES_DATA_DIR}/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF'
TIME_REGEX = '[0-9]{8}'


class TestMosaicWithoutTime(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.LAYER_TYPE
    rest_parametrization = []
    test_cases = [
        base_test.TestCaseType(
            key='patch_single_raster_to_mosaic_without_time',
            type=base_test.EnumTestTypes.MANDATORY,
            publication=Publication4Test(
                type=process_client.LAYER_TYPE,
                workspace=WORKSPACE,
                name='patch_single_raster_to_mosaic_without_time',
            ),
            rest_method=base_test.RestMethod.PATCH,
            rest_args={
                'file_paths': [MOSAIC_RASTER_1, MOSAIC_RASTER_2],
            },
            post_before_test_args={
                'file_paths': [MOSAIC_RASTER_1],
            },
            params={
                'expect_image_mosaic': True,
                'expect_wms_time': False,
                'exp_info': {
                    'exp_publication_detail': {
                        'bounding_box': [1765989.8419897896, 6475062.528006903, 1766372.3874324549, 6475719.834424445],
                        'geodata_type': 'raster',
                        'image_mosaic': True,
                        'native_bounding_box': [-639320.0, -1047442.0, -639120.0, -1047042.0],
                        'native_crs': 'EPSG:5514',
                    },
                    'publ_type_detail': ('raster', 'sld'),
                },
                'filenames': ['1.tif', '2.tif'],
                'exp_thumbnail': os.path.join(DIRECTORY, 'thumbnail_mosaic_without_time_lesprojekt.png'),
                'thumbnail_max_diffs': 10,
            },
        ),
        base_test.TestCaseType(
            key='patch_timeseries_to_mosaic_without_time',
            type=base_test.EnumTestTypes.MANDATORY,
            publication=Publication4Test(
                type=process_client.LAYER_TYPE,
                workspace=WORKSPACE,
                name='patch_timeseries_to_mosaic_without_time',
            ),
            rest_method=base_test.RestMethod.PATCH,
            rest_args={
                'file_paths': [TIMESERIES_RASTER_20220316, TIMESERIES_RASTER_20220319],
            },
            post_before_test_args={
                'file_paths': [TIMESERIES_RASTER_20220316, TIMESERIES_RASTER_20220319],
                'time_regex': TIME_REGEX,
            },
            params={
                'expect_image_mosaic': True,
                'expect_wms_time': False,
                'exp_info': {
                    'exp_publication_detail': {
                        'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                        'geodata_type': 'raster',
                        'image_mosaic': True,
                        'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                        'native_crs': 'EPSG:32633',
                    },
                    'publ_type_detail': ('raster', 'sld'),
                },
                'filenames': [
                    'S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                    'S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF',
                ],
            },
        ),
        base_test.TestCaseType(
            key='patch_mosaic_without_time_to_single_raster',
            type=base_test.EnumTestTypes.MANDATORY,
            publication=Publication4Test(
                type=process_client.LAYER_TYPE,
                workspace=WORKSPACE,
                name='patch_mosaic_without_time_to_single_raster',
            ),
            rest_method=base_test.RestMethod.PATCH,
            rest_args={
                'file_paths': [MOSAIC_RASTER_1],
            },
            post_before_test_args={
                'file_paths': [MOSAIC_RASTER_1, MOSAIC_RASTER_2],
            },
            params={
                'expect_image_mosaic': False,
                'expect_wms_time': False,
                'exp_info': {
                    'exp_publication_detail': {
                        'bounding_box': [1765989.8419897896, 6475372.857587902, 1766335.862065537, 6475719.834424445],
                        'geodata_type': 'raster',
                        'image_mosaic': False,
                        'native_bounding_box': [-639320.0, -1047242.0, -639120.0, -1047042.0],
                        'native_crs': 'EPSG:5514',
                    },
                    'publ_type_detail': ('raster', 'sld'),
                },
                'file_extension': 'tif',
            },
        ),
        base_test.TestCaseType(
            key='patch_mosaic_without_time_to_timeseries',
            type=base_test.EnumTestTypes.MANDATORY,
            publication=Publication4Test(
                type=process_client.LAYER_TYPE,
                workspace=WORKSPACE,
                name='patch_mosaic_without_time_to_timeseries',
            ),
            rest_method=base_test.RestMethod.PATCH,
            rest_args={
                'file_paths': [TIMESERIES_RASTER_20220316, TIMESERIES_RASTER_20220319],
                'time_regex': TIME_REGEX,
            },
            post_before_test_args={
                'file_paths': [TIMESERIES_RASTER_20220316, TIMESERIES_RASTER_20220319],
            },
            params={
                'expect_image_mosaic': True,
                'expect_wms_time': True,
                'exp_info': {
                    'exp_publication_detail': {
                        'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                        'geodata_type': 'raster',
                        'image_mosaic': True,
                        'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                        'native_crs': 'EPSG:32633',
                        'wms': {
                            'time': {
                                'default': '2022-03-19T00:00:00.000Z',
                                'regex': TIME_REGEX,
                                'units': 'ISO8601',
                                'values': ['2022-03-16T00:00:00.000Z', '2022-03-19T00:00:00.000Z'],
                            }
                        },
                    },
                    'publ_type_detail': ('raster', 'sld'),
                },
                'filenames': [
                    'S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                    'S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF',
                ],
            },
        ),
    ]

    def test_mosaic_without_time_patch_transitions(self, layer, rest_method, rest_args, params):
        rest_method.fn(layer, args=rest_args)
        assert_util.is_publication_valid_and_complete(layer)

        with app.app_context():
            pub_info = layman_util.get_publication_info(layer.workspace, layer.type, layer.name)
            assert pub_info.get('image_mosaic') is params['expect_image_mosaic']
            if params['expect_wms_time']:
                assert 'time' in pub_info.get('wms', {}), 'Timeseries layer must expose WMS time dimension'
                time_values = pub_info['wms']['time']['values']
                assert len(time_values) >= 2, f'Expected at least two time instants, got {time_values}'
            else:
                assert 'time' not in pub_info.get('wms', {}), 'Non-timeseries mosaic must not expose WMS time dimension'

        asserts_publ.internal.correct_values_in_detail(
            layer.workspace, layer.type, layer.name,
            full_comparison=True,
            **params['exp_info'],
            filenames=params.get('filenames'),
            file_extension=params.get('file_extension'),
        )
        exp_thumbnail = params.get('exp_thumbnail')
        if exp_thumbnail:
            assert os.path.exists(exp_thumbnail), f'Expected thumbnail is missing: {exp_thumbnail}'
            asserts_publ.internal.thumbnail_equals(
                layer.workspace,
                layer.type,
                layer.name,
                exp_thumbnail,
                max_diffs=params.get('thumbnail_max_diffs', 1),
            )
