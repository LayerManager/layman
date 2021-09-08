from layman import settings

DEFINITION = 'definition'
TEST_DATA = 'test_data'


LAYER_DEFINITIONS = [
    {
            DEFINITION: {'file_paths': ['sample/layman.layer/sample_png_pgw_rgba.pgw',
                                        'sample/layman.layer/sample_png_pgw_rgba.png', ]},
            TEST_DATA:{
                'expected_exc': {'http_code': 400,
                                 'code': 4,
                                 'message': 'Unsupported CRS of data file',
                                 'detail': {'found': 'None', 'supported_values': settings.INPUT_SRS_LIST},
                                 },
                'error_async_part': 'file',
            }
    },
]
