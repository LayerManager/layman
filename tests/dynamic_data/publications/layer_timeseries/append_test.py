import os

from layman import app
from layman import util as layman_util
from layman.layer.filesystem import gdal
from test_tools import process_client
from tests import EnumTestTypes, Publication4Test
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

INITIAL_FILE_16 = os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif')
INITIAL_FILE_22 = os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220322T100031_N0400_R122_T33UWR_20220322T134748_TCI_10m.tif')
APPEND_FILE_19 = os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF')


class TimeRegexFormatDomain(base_test.CompressDomainBase):
    WITHOUT_FORMAT = (False, None)
    WITH_FORMAT = (False, None, {'time_regex_format': 'yyyyMMdd'})


PUBLICATIONS = {
    'append_test': {
        'title': 'Timeseries Layer Append Test',
        'time_regex': r'[0-9]{8}',
        'file_paths': [INITIAL_FILE_16, INITIAL_FILE_22],
    },
}


def generate_test_cases():
    from tests.dynamic_data.base_test_classes import TestCaseType
    tc_list = []
    for key, params in PUBLICATIONS.items():
        rest_args = {
            'time_regex': params['time_regex'],
            'file_paths': params['file_paths'],
        }
        test_case = TestCaseType(
            key=key,
            type=EnumTestTypes.MANDATORY,
            rest_args=rest_args,
        )
        tc_list.append(test_case)
    return tc_list


class TestLayerAppend(base_test.TestSingleRestPublication):
    workspace = 'timeseries_layer_append'
    publication_type = process_client.LAYER_TYPE
    rest_parametrization = [
        base_test.RestMethod,
        base_test.RestArgs.WITH_CHUNKS,
        TimeRegexFormatDomain,
    ]
    test_cases = generate_test_cases()

    def _assert_timeseries_layer_state(self, workspace, layer_name, expected_file_basenames, expected_time_values):
        with app.app_context():
            info = process_client.get_workspace_layer(workspace, layer_name)

        assert info['image_mosaic'] is True
        assert 'wms' in info

        file_paths = info['file']['paths']
        path_filenames = [os.path.basename(path) for path in file_paths]
        for expected_filename in expected_file_basenames:
            assert expected_filename in path_filenames, f"Expected file {expected_filename} not found in paths: {path_filenames}"

        wms_time_values = info['wms']['time']['values']
        assert len(wms_time_values) == len(expected_time_values), \
            f"Expected {len(expected_time_values)} time values, got {len(wms_time_values)}: {wms_time_values}"
        assert wms_time_values == expected_time_values, \
            f"Expected time values {expected_time_values}, got {wms_time_values}"

    def test_timeseries_append_flow(self, layer: Publication4Test, rest_method, rest_args):
        with_chunks = rest_args.get('with_chunks', False)
        upload_type = "chunk" if with_chunks else "direct"
        app.logger.info(f"Upload type: {upload_type}")

        if rest_method.enum_item != base_test.RestMethod.POST:
            app.logger.info(f"Skipping test for method: {rest_method.enum_item}")
            return

        rest_method.fn(layer, args=rest_args)
        name = layer.name

        initial_file_basenames = [
            os.path.basename(INITIAL_FILE_16),
            os.path.basename(INITIAL_FILE_22),
        ]
        expected_times_before = ['2022-03-16T00:00:00.000Z', '2022-03-22T00:00:00.000Z']
        self._assert_timeseries_layer_state(self.workspace, name, initial_file_basenames, expected_times_before)

        with app.app_context():
            uuid = layman_util.get_publication_uuid(self.workspace, process_client.LAYER_TYPE, name)
        normalized_filepaths_before = gdal.get_normalized_raster_layer_main_filepaths(uuid)
        file_timestamps_before = {os.path.basename(fp): os.path.getmtime(fp) for fp in normalized_filepaths_before}

        append_file = APPEND_FILE_19
        patch_args = {
            'file_paths': [append_file],
            'append': True,
            'with_chunks': with_chunks,
        }
        process_client.patch_workspace_layer(self.workspace, name, **patch_args)

        all_file_basenames = initial_file_basenames + [os.path.basename(append_file)]
        expected_times_after = ['2022-03-16T00:00:00.000Z', '2022-03-19T00:00:00.000Z', '2022-03-22T00:00:00.000Z']
        self._assert_timeseries_layer_state(self.workspace, name, all_file_basenames, expected_times_after)

        normalized_filepaths_after = gdal.get_normalized_raster_layer_main_filepaths(uuid)
        file_timestamps_after = {os.path.basename(fp): os.path.getmtime(fp) for fp in normalized_filepaths_after}
        for filename, timestamp_before in file_timestamps_before.items():
            assert filename in file_timestamps_after, f"File {filename} not found after append"
            timestamp_after = file_timestamps_after[filename]
            assert timestamp_before == timestamp_after, \
                f"Timestamp of existing file {filename} changed: before={timestamp_before}, after={timestamp_after}. " \
                f"File was regenerated instead of being preserved."
