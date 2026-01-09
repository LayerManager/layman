import os
import pytest

from layman import LaymanError
from test_tools import process_client

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

INITIAL_FILE_16 = os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif')
APPEND_FILE_19 = os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF')

NEGATIVE_TEST_CASES = {
    'append_without_file': {
        'setup': {
            'file_paths': [INITIAL_FILE_16],
            'time_regex': r'[0-9]{8}',
        },
        'append_args': {
            'append': True,
        },
        'expected_error': {
            'code': 48,
            'http_code': 400,
            'data_check': lambda data: (
                ('append' in str(data.get('parameter', '')) if isinstance(data, dict) else 'append' in str(data))
                and ('file' in str(data.get('message', '')) if isinstance(data, dict) else 'file' in str(data))
            ),
        },
    },
    'append_on_non_timeseries_layer': {
        'setup': {
            'file_paths': [INITIAL_FILE_16],
        },
        'append_args': {
            'file_paths': [APPEND_FILE_19],
            'append': True,
        },
        'expected_error': {
            'code': 48,
            'http_code': 400,
            'data_check': lambda data: (
                (data.get('parameter') == 'append' if isinstance(data, dict) else False)
                and ('timeseries' in str(data.get('message', '')) if isinstance(data, dict) else 'timeseries' in str(data))
            ),
        },
    },
    'append_with_time_regex_provided': {
        'setup': {
            'file_paths': [INITIAL_FILE_16],
            'time_regex': r'[0-9]{8}',
        },
        'append_args': {
            'file_paths': [APPEND_FILE_19],
            'append': True,
            'time_regex': r'[0-9]{8}',
        },
        'expected_error': {
            'code': 48,
            'http_code': 400,
            'data_check': lambda data: (
                (data.get('parameter') == 'time_regex' if isinstance(data, dict) else False)
                and ('not allowed' in str(data.get('message', '')) if isinstance(data, dict) else 'not allowed' in str(data))
            ),
        },
    },
    'append_on_nonexistent_layer': {
        'setup': None,
        'append_args': {
            'file_paths': [APPEND_FILE_19],
            'append': True,
        },
        'expected_error': {
            'code': 15,
            'http_code': 404,
            'data_check': lambda data: True,
        },
        'layer_name': 'nonexistent_layer_12345',
    },
}

WORKSPACE = 'dynamic_test_workspace_timeseries_layer_append'


@pytest.mark.usefixtures('ensure_layman_module')
@pytest.mark.parametrize('test_case_key', list(NEGATIVE_TEST_CASES.keys()))
def test_append_negative(test_case_key):
    test_case = NEGATIVE_TEST_CASES[test_case_key]
    layer_name = test_case.get('layer_name', f'test_append_{test_case_key}')

    if test_case['setup']:
        process_client.publish_workspace_layer(
            WORKSPACE, layer_name,
            **test_case['setup']
        )

    expected_error = test_case['expected_error']
    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_layer(
            WORKSPACE, layer_name,
            **test_case['append_args']
        )

    assert exc_info.value.code == expected_error['code']
    assert exc_info.value.http_code == expected_error['http_code']
    data_check_result = expected_error['data_check'](exc_info.value.data)
    assert data_check_result, \
        f"Error data check failed for {test_case_key}: {exc_info.value.data}, check_result={data_check_result}"

    if test_case['setup']:
        process_client.delete_workspace_layer(WORKSPACE, layer_name)
