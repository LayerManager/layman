from layman import settings

DEFINITION = 'definition'
TEST_DATA = 'test_data'

ASYNC_ERROR = 'async_error'
SYNC_ERROR = 'sync_error'

LAYER_DEFINITIONS = [
    {
        DEFINITION: {'file_paths': ['sample/layman.layer/sample_png_pgw_rgba.pgw',
                                    'sample/layman.layer/sample_png_pgw_rgba.png', ]},
        TEST_DATA: {
            'expected_exc': {'http_code': 400,
                             'code': 4,
                             'message': 'Unsupported CRS of data file',
                             'detail': {'found': 'None', 'supported_values': settings.INPUT_SRS_LIST},
                             },
            'error_async_part': 'file',
            'chunk_error_type': ASYNC_ERROR,
        }
    },
    {
        DEFINITION: {'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
                     'style_file': 'sample/style/ne_10m_admin_0_countries.qml'},
        TEST_DATA: {
            'expected_exc': {'http_code': 400,
                             'code': 48,
                             'message': 'Wrong combination of parameters',
                             'detail': 'Raster layers are not allowed to have QML style.',
                             },
            'error_async_part': 'file',
            'chunk_error_type': SYNC_ERROR,
        }
    },
]

LAYER_CHUNK_ASYNC_ERROR_DEFINITIONS = [layer_def for layer_def in LAYER_DEFINITIONS
                                       if layer_def[TEST_DATA]['chunk_error_type'] == ASYNC_ERROR]
LAYER_CHUNK_SYNC_ERROR_DEFINITIONS = [layer_def for layer_def in LAYER_DEFINITIONS
                                      if layer_def[TEST_DATA]['chunk_error_type'] == SYNC_ERROR]
