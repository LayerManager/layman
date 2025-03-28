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
    'more_files_zip': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'rest_args': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF'),
            ],
            'compress': True,
            'compress_settings': process_client.CompressTypeDef(archive_name='timeseries_tif',
                                                                inner_directory='/timeseries_tif/',
                                                                file_name=None,
                                                                ),
        },
        'do_complex_test': True,
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                'image_mosaic': True,
                'wms': {
                    'time': {'default': '2022-03-19T00:00:00.000Z',
                             'units': 'ISO8601',
                             'regex': r'[0-9]{8}',
                             'values': ['2022-03-16T00:00:00.000Z',
                                        '2022-03-19T00:00:00.000Z']},
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'gdal_prefix': '/vsizip/',
            'archive_extension': 'zip',
            'filenames': [
                'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF',
            ]
        },
        'expected_thumbnail': os.path.join(DIRECTORY, 'thumbnail_timeseries.png'),
        'wms_bbox': [1743913.19942603237, 6499107.284021802247, 1755465.937341974815, 6503948.597792930901, ],
    },
    'more_files': {
        'rest_args': {
            'time_regex': r'^.*([0-9]{4})([0-9]{2})([0-9]{2}).*$',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031.0.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031.1.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031.2.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031.3.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731.0.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731.1.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731.2.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731.3.tif'),
            ],
        },
        'do_complex_test': True,
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                'image_mosaic': True,
                'wms': {
                    'time': {'default': '2022-03-19T00:00:00.000Z',
                             'units': 'ISO8601',
                             'regex': r'^.*([0-9]{4})([0-9]{2})([0-9]{2}).*$',
                             'values': ['2022-03-16T00:00:00.000Z',
                                        '2022-03-19T00:00:00.000Z']},
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'filenames': [
                'S2A_MSIL2A_20220316T100031.0.tif',
                'S2A_MSIL2A_20220316T100031.1.tif',
                'S2A_MSIL2A_20220316T100031.2.tif',
                'S2A_MSIL2A_20220316T100031.3.tif',
                'S2A_MSIL2A_20220319T100731.0.tif',
                'S2A_MSIL2A_20220319T100731.1.tif',
                'S2A_MSIL2A_20220319T100731.2.tif',
                'S2A_MSIL2A_20220319T100731.3.tif',
            ],
        },
        'wms_bbox': [1743913.19942603237, 6499107.284021802247, 1755465.937341974815, 6503948.597792930901, ],
    },
    'longname_one_file_compressed': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'rest_args': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY,
                             'timeseries_tif/210_long_name_20221031_sample_jpg_aux_rgba_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpeg',
                             ),
                os.path.join(DIRECTORY,
                             'timeseries_tif/210_long_name_20221031_sample_jpg_aux_rgba_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpeg.aux.xml',
                             ),
            ],
            'compress': True,
            'compress_settings': process_client.CompressTypeDef(archive_name='210_long_name_20221031_sample_jpg_aux_rgba_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                                                                inner_directory='/timeseries_tif/',
                                                                file_name=None,
                                                                ),
        },
        'do_complex_test': False,
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [2707260.9569237595, 7740717.799460372, 2708414.90486888, 7741573.954387397],
                'native_crs': 'EPSG:3857',
                'native_bounding_box': [2707260.9569237595, 7740717.799460372, 2708414.90486888, 7741573.954387397],
                'image_mosaic': True,
                'wms': {
                    'time': {'default': '2022-10-31T00:00:00.000Z',
                             'units': 'ISO8601',
                             'regex': r'[0-9]{8}',
                             'values': ['2022-10-31T00:00:00.000Z']},
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'gdal_prefix': '/vsizip/',
            'archive_extension': 'zip',
            'filenames': [
                'timeseries_tif/210_long_name_20221031_sample_jpg_aux_rgba_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpeg',
            ]
        },
    },
    'longname_one_file': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'rest_args': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY,
                             'timeseries_tif/210_long_name_20221031_sample_jpg_aux_rgba_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpeg',
                             ),
                os.path.join(DIRECTORY,
                             'timeseries_tif/210_long_name_20221031_sample_jpg_aux_rgba_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpeg.aux.xml',
                             ),
            ],
            'compress': False,
        },
        'do_complex_test': False,
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [2707260.9569237595, 7740717.799460372, 2708414.90486888, 7741573.954387397],
                'native_crs': 'EPSG:3857',
                'native_bounding_box': [2707260.9569237595, 7740717.799460372, 2708414.90486888, 7741573.954387397],
                'image_mosaic': True,
                'wms': {
                    'time': {'default': '2022-10-31T00:00:00.000Z',
                             'units': 'ISO8601',
                             'regex': r'[0-9]{8}',
                             'values': ['2022-10-31T00:00:00.000Z']},
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'filenames': [
                '210_long_name_20221031_sample_jpg_aux_rgba_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpeg',
            ]
        },
    },
    'diacritics_and_spaces_zip': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'rest_args': {
            'time_regex': r'^Cerekvice nad Bystřicí ([0-9]{8}).*$',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries_tif/Cerekvice nad Bystřicí 20220316.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/Cerekvice nad Bystřicí 20220319.TIF'),
            ],
            'compress': True,
            'compress_settings': process_client.CompressTypeDef(archive_name='timeseries_tif',
                                                                inner_directory='/timeseries_tif/',
                                                                file_name=None,
                                                                ),
        },
        'do_complex_test': False,
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                'image_mosaic': True,
                'wms': {
                    'time': {'default': '2022-03-19T00:00:00.000Z',
                             'units': 'ISO8601',
                             'regex': r'^Cerekvice_nad_Bystrici_([0-9]{8}).*$',
                             'values': ['2022-03-16T00:00:00.000Z',
                                        '2022-03-19T00:00:00.000Z']},
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'gdal_prefix': '/vsizip/',
            'archive_extension': 'zip',
            'filenames': [
                'timeseries_tif/Cerekvice nad Bystřicí 20220316.tif',
                'timeseries_tif/Cerekvice nad Bystřicí 20220319.TIF',
            ]
        },
    },
    'diacritics_and_spaces': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'rest_args': {
            'time_regex': r'^Cerekvice nad Bystřicí ([0-9]{8}).*$',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries_tif/Cerekvice nad Bystřicí 20220316.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/Cerekvice nad Bystřicí 20220319.TIF'),
            ],
            'compress': False,
        },
        'do_complex_test': False,
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                'image_mosaic': True,
                'wms': {
                    'time': {'default': '2022-03-19T00:00:00.000Z',
                             'units': 'ISO8601',
                             'regex': r'^Cerekvice_nad_Bystrici_([0-9]{8}).*$',
                             'values': ['2022-03-16T00:00:00.000Z',
                                        '2022-03-19T00:00:00.000Z']},
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'filenames': [
                'Cerekvice_nad_Bystrici_20220316.tif',
                'Cerekvice_nad_Bystrici_20220319.TIF',
            ]
        },
    },
    'one_file_format_simple': {
        'rest_args': {
            'time_regex': r'^.*([0-9]{4})([0-9]{2})([0-9]{2}).*$',
            'time_regex_format': 'yyyyddMM',
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
    'one_file_format_complex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'rest_args': {
            'time_regex': r'^.*([0-9]{4} [0-9]{2}_[0-9]{2}at[0-9]{2}-[0-9]{2}).*$',
            'time_regex_format': "yyyy dd_MM'at'HH-mm",
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_2022 16_03at10-00.tif'),
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
                    'time': {'default': '2022-03-16T00:00:00.000Z',  # https://github.com/LayerManager/layman/issues/875
                             'units': 'ISO8601',
                             'regex': "^.*([0-9]{4}_[0-9]{2}_[0-9]{2}at[0-9]{2}-[0-9]{2}).*$",
                             'regex_format': "yyyy_dd_MM'at'HH-mm",
                             'values': ['2022-03-16T00:00:00.000Z']},  # https://github.com/LayerManager/layman/issues/875
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'filenames': [
                'S2A_MSIL2A_2022_16_03at10-00.tif',
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
        base_test.RestMethod,
        base_test.RestArgs.WITH_CHUNKS,
    ]

    test_cases = generate_test_cases()

    @pytest.mark.timeout(60)
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
