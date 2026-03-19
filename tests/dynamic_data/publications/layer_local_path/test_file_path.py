import os
import shutil
import glob
import pytest

from layman import LaymanError, settings, app, util as layman_util
from test_tools import process_client
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test
from tests import Publication4Test

pytest_generate_tests = base_test.pytest_generate_tests
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = "test_file_path_ws"


TEST_UUID_MOSAIC = '4d2ee21d-f7d9-4f16-a191-f15637c94c96'
TEST_UUID_SINGLE = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'


@pytest.fixture(scope='class')
def prepare_file_path_data():
    normalized_raster_data_dir = settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR
    assert os.path.exists(normalized_raster_data_dir), \
        f"Normalized raster data directory not found: {normalized_raster_data_dir}."

    layers_dir = os.path.join(normalized_raster_data_dir, 'layers')
    target_dirs = []

    source_dir_mosaic = os.path.join(DIRECTORY, 'layers', TEST_UUID_MOSAIC)

    target_dir_mosaic = os.path.join(layers_dir, TEST_UUID_MOSAIC)
    if os.path.exists(target_dir_mosaic):
        shutil.rmtree(target_dir_mosaic)
    os.makedirs(layers_dir, exist_ok=True)
    assert os.path.exists(source_dir_mosaic), f"Source directory does not exist: {source_dir_mosaic}"
    shutil.copytree(source_dir_mosaic, target_dir_mosaic)
    tif_files = glob.glob(os.path.join(target_dir_mosaic, '*.tif'))
    assert tif_files, f"No .tif files found in target directory: {target_dir_mosaic}."
    timeregex_file = os.path.join(target_dir_mosaic, 'timeregex.properties')
    assert os.path.exists(timeregex_file), f"timeregex.properties not found in target directory: {target_dir_mosaic}."
    target_dirs.append(target_dir_mosaic)

    target_dir_single = os.path.join(layers_dir, TEST_UUID_SINGLE)
    if os.path.exists(target_dir_single):
        shutil.rmtree(target_dir_single)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(DIRECTORY))))
    sample_file = os.path.join(base_dir, 'sample', 'layman.layer', 'sample_tif_rgb.tif')
    assert os.path.exists(sample_file), f"Sample raster file not found. This is a test setup error."

    os.makedirs(target_dir_single, exist_ok=True)
    target_file = os.path.join(target_dir_single, 'raster.tif')
    shutil.copy2(sample_file, target_file)
    target_dirs.append(target_dir_single)

    yield

    for target_dir in target_dirs:
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir, ignore_errors=True)
            except Exception:
                pass


def generate_test_cases():
    normalized_raster_data_dir_name = settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR_NAME
    test_cases = []

    file_path_relative_mosaic = os.path.join(
        normalized_raster_data_dir_name,
        'layers',
        TEST_UUID_MOSAIC
    )
    publication_mosaic = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_mosaic',
    )
    test_case_mosaic = base_test.TestCaseType(
        key='file_path_mosaic',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_mosaic,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': file_path_relative_mosaic,
            'time_regex': '[0-9]{8}',
        },
        params={
            'exp_info': {
                'exp_publication_detail': {
                    'geodata_type': 'raster',
                    'image_mosaic': True,
                },
                'publ_type_detail': ('raster', 'sld'),
            },
            'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tif.png',
        },
    )
    test_cases.append(test_case_mosaic)

    file_path_relative_single = os.path.join(
        normalized_raster_data_dir_name,
        'layers',
        TEST_UUID_SINGLE
    )
    publication_single = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_single',
    )
    test_case_single = base_test.TestCaseType(
        key='file_path_single',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_single,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': file_path_relative_single,
        },
        params={
            'exp_info': {
                'exp_publication_detail': {
                    'geodata_type': 'raster',
                    'image_mosaic': False,
                },
                'publ_type_detail': ('raster', 'sld'),
            },
            'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tif.png',
        },
    )
    test_cases.append(test_case_single)

    file_path_relative_single_file = os.path.join(
        normalized_raster_data_dir_name,
        'layers',
        TEST_UUID_SINGLE,
        'raster.tif',
    )
    publication_single_file = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_single_file',
    )
    test_case_single_file = base_test.TestCaseType(
        key='file_path_single_file',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_single_file,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': file_path_relative_single_file,
        },
        params={
            'exp_info': {
                'exp_publication_detail': {
                    'geodata_type': 'raster',
                    'image_mosaic': False,
                },
                'publ_type_detail': ('raster', 'sld'),
            },
            'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tif.png',
        },
    )
    test_cases.append(test_case_single_file)

    return test_cases


@pytest.mark.usefixtures('prepare_file_path_data')
class TestFilePath(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.LAYER_TYPE
    rest_parametrization = []
    test_cases = generate_test_cases()

    def test_file_path(self, layer, rest_args, params):
        self.post_publication(layer, args=rest_args)

        assert_util.is_publication_valid_and_complete(layer)

        with app.app_context():
            pub_info = layman_util.get_publication_info(layer.workspace, layer.type, layer.name)
            if params['exp_info']['exp_publication_detail'].get('image_mosaic'):
                assert 'wms' in pub_info and 'time' in pub_info['wms'], \
                    "Timeseries layer (image_mosaic=True) must expose WMS time dimension"
            assert 'bounding_box' in pub_info, "Layer must have bounding_box"
            assert 'native_bounding_box' in pub_info, "Layer must have native_bounding_box"
            assert 'native_crs' in pub_info, "Layer must have native_crs"
            assert 'file_path' in pub_info, "Layer must have file_path key in GET response"
            assert pub_info['file_path'] == rest_args['file_path'], \
                f"file_path in response ({pub_info['file_path']}) must match requested file_path ({rest_args['file_path']})"

        asserts_publ.internal.correct_values_in_detail(
            layer.workspace, layer.type, layer.name,
            full_comparison=False,
            **params['exp_info']
        )

        asserts_publ.internal.thumbnail_equals(
            layer.workspace, layer.type, layer.name,
            exp_thumbnail=params['exp_thumbnail'],
            max_diffs=100000
        )


def generate_negative_test_cases():
    normalized_raster_data_dir_name = settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR_NAME
    test_cases = []

    publication_abs = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_absolute',
    )
    test_case_abs = base_test.TestCaseType(
        key='file_path_absolute',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_abs,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': '/absolute/path/to/directory',
        },
        params={
            'should_succeed': False,
            'expected_error_code': 2,
            'expected_error_param': 'file_path',
        },
    )
    test_cases.append(test_case_abs)

    publication_nonexistent = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_nonexistent',
    )
    test_case_nonexistent = base_test.TestCaseType(
        key='file_path_nonexistent',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_nonexistent,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': os.path.join(normalized_raster_data_dir_name, 'layers', 'nonexistent_uuid'),
        },
        params={
            'should_succeed': False,
            'expected_error_code': 2,
            'expected_error_param': 'file_path',
        },
    )
    test_cases.append(test_case_nonexistent)

    publication_no_tif = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_no_tif',
    )
    test_case_no_tif = base_test.TestCaseType(
        key='file_path_no_tif',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_no_tif,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': os.path.join(normalized_raster_data_dir_name, 'layers', 'empty_dir'),
        },
        params={
            'should_succeed': False,
            'expected_error_code': 2,
            'expected_error_param': 'file_path',
        },
    )
    test_cases.append(test_case_no_tif)

    publication_file_unsupported = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_file_unsupported',
    )
    test_case_file_unsupported = base_test.TestCaseType(
        key='file_path_file_unsupported',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_file_unsupported,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': os.path.join(normalized_raster_data_dir_name, 'layers', 'unsupported_file', 'raster.png'),
        },
        params={
            'should_succeed': False,
            'expected_error_code': 2,
            'expected_error_param': 'file_path',
        },
    )
    test_cases.append(test_case_file_unsupported)

    publication_vector_file = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_vector_file',
    )
    test_case_vector_file = base_test.TestCaseType(
        key='file_path_vector_file',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_vector_file,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': os.path.join(normalized_raster_data_dir_name, 'layers', 'vector_file', 'sample.shp'),
        },
        params={
            'should_succeed': False,
            'expected_error_code': 2,
            'expected_error_param': 'file_path',
        },
    )
    test_cases.append(test_case_vector_file)

    publication_no_regex = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_no_regex',
    )
    test_case_no_regex = base_test.TestCaseType(
        key='file_path_no_regex',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_no_regex,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': os.path.join(normalized_raster_data_dir_name, 'layers', 'multi_no_regex'),
        },
        params={
            'should_succeed': False,
            'expected_error_code': 48,
            'expected_error_params': ['file_path', 'time_regex'],
        },
    )
    test_cases.append(test_case_no_regex)

    publication_file_with_regex = Publication4Test(
        type=process_client.LAYER_TYPE,
        workspace=WORKSPACE,
        name='test_file_path_file_with_regex',
    )
    test_case_file_with_regex = base_test.TestCaseType(
        key='file_path_file_with_regex',
        type=base_test.EnumTestTypes.MANDATORY,
        publication=publication_file_with_regex,
        rest_method=base_test.RestMethod.POST,
        rest_args={
            'file_path': os.path.join(normalized_raster_data_dir_name, 'layers', TEST_UUID_SINGLE, 'raster.tif'),
            'time_regex': '[0-9]{8}',
        },
        params={
            'should_succeed': False,
            'expected_error_code': 48,
            'expected_error_params': ['file_path', 'time_regex'],
        },
    )
    test_cases.append(test_case_file_with_regex)

    return test_cases


@pytest.fixture(scope='class')
def prepare_negative_test_data():
    normalized_raster_data_dir = settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR
    assert os.path.exists(normalized_raster_data_dir), \
        f"Normalized raster data directory not found: {normalized_raster_data_dir}."

    layers_dir = os.path.join(normalized_raster_data_dir, 'layers')
    target_dirs = []

    empty_dir = os.path.join(layers_dir, 'empty_dir')
    if os.path.exists(empty_dir):
        shutil.rmtree(empty_dir)
    os.makedirs(empty_dir, exist_ok=True)
    target_dirs.append(empty_dir)

    multi_no_regex_dir = os.path.join(layers_dir, 'multi_no_regex')
    if os.path.exists(multi_no_regex_dir):
        shutil.rmtree(multi_no_regex_dir)
    os.makedirs(multi_no_regex_dir, exist_ok=True)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(DIRECTORY))))
    sample_file = os.path.join(base_dir, 'sample', 'layman.layer', 'sample_tif_rgb.tif')
    assert os.path.exists(sample_file), f"Sample raster file not found: {sample_file}"
    shutil.copy2(sample_file, os.path.join(multi_no_regex_dir, 'raster1.tif'))
    shutil.copy2(sample_file, os.path.join(multi_no_regex_dir, 'raster2.tif'))
    target_dirs.append(multi_no_regex_dir)

    unsupported_file_dir = os.path.join(layers_dir, 'unsupported_file')
    if os.path.exists(unsupported_file_dir):
        shutil.rmtree(unsupported_file_dir)
    os.makedirs(unsupported_file_dir, exist_ok=True)
    with open(os.path.join(unsupported_file_dir, 'raster.png'), 'wb') as unsupported_file:
        unsupported_file.write(b'not-a-geotiff')
    target_dirs.append(unsupported_file_dir)

    vector_file_dir = os.path.join(layers_dir, 'vector_file')
    if os.path.exists(vector_file_dir):
        shutil.rmtree(vector_file_dir)
    os.makedirs(vector_file_dir, exist_ok=True)
    source_shp = os.path.join(DIRECTORY, 'layers', TEST_UUID_MOSAIC, f'{TEST_UUID_MOSAIC}.shp')
    assert os.path.exists(source_shp), f"Sample vector file not found: {source_shp}"
    shutil.copy2(source_shp, os.path.join(vector_file_dir, 'sample.shp'))
    target_dirs.append(vector_file_dir)

    single_file_for_regex_conflict_dir = os.path.join(layers_dir, TEST_UUID_SINGLE)
    if os.path.exists(single_file_for_regex_conflict_dir):
        shutil.rmtree(single_file_for_regex_conflict_dir)
    os.makedirs(single_file_for_regex_conflict_dir, exist_ok=True)
    shutil.copy2(sample_file, os.path.join(single_file_for_regex_conflict_dir, 'raster.tif'))
    target_dirs.append(single_file_for_regex_conflict_dir)

    yield

    for target_dir in target_dirs:
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir, ignore_errors=True)
            except Exception:
                pass


@pytest.mark.usefixtures('prepare_negative_test_data')
class TestFilePathNegative(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.LAYER_TYPE
    rest_parametrization = []
    test_cases = generate_negative_test_cases()

    def test_file_path_negative(self, layer, rest_args, params):
        should_succeed = params.get('should_succeed', True)

        assert not should_succeed, "Negative test case should have should_succeed=False"

        expected_error_code = params.get('expected_error_code')
        expected_error_param = params.get('expected_error_param')
        expected_error_params = params.get('expected_error_params')

        with pytest.raises(LaymanError) as exc_info:
            self.post_publication(layer, args=rest_args)

        error = exc_info.value
        assert error.code == expected_error_code, \
            f"Expected error code {expected_error_code}, got {error.code}. Error: {error.data}"
        assert error.http_code == 400, \
            f"Expected HTTP code 400, got {error.http_code}"

        if expected_error_param:
            assert error.data.get('parameter') == expected_error_param, \
                f"Expected parameter '{expected_error_param}', got '{error.data.get('parameter')}'"

        if expected_error_params:
            assert error.data.get('parameters') == expected_error_params, \
                f"Expected parameters {expected_error_params}, got {error.data.get('parameters')}"
