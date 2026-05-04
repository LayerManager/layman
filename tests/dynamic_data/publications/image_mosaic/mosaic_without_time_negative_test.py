import pytest

from layman.http import LaymanError
from test_tools import process_client

WORKSPACE = 'dynamic_test_workspace_mosaic_without_time_negative'


NEGATIVE_TEST_CASES = {
    'mixed_main_extensions': {
        'file_paths': [
            'sample/layman.layer/sample_jp2_j2w_rgb.j2w',
            'sample/layman.layer/sample_jp2_j2w_rgb.jp2',
            'sample/layman.layer/sample_jpeg_jgw_rgb.jgw',
            'sample/layman.layer/sample_jpeg_jgw_rgb.jpeg',
        ],
        'expected': 'All main files with the same extension.',
    },
    'different_crs': {
        'file_paths': [
            'tests/dynamic_data/publications/crs/rasters/cz_4326.tif',
            'tests/dynamic_data/publications/crs/rasters/cz_32633.tif',
        ],
        'expected': 'All main files with the same CRS.',
    },
    'different_bands': {
        'file_paths': [
            'sample/layman.layer/sample_tif_rgba.tif',
            'sample/layman.layer/sample_tif_rgb_nodata.tif',
        ],
        'expected': 'All main files with the same color interpretations.',
    },
}


@pytest.mark.usefixtures('ensure_layman_module')
@pytest.mark.parametrize(('case_key', 'case'), NEGATIVE_TEST_CASES.items())
def test_mosaic_without_time_negative(case_key, case):
    layer_name = f'mosaic_without_time_negative_{case_key}'
    try:
        with pytest.raises(LaymanError) as exc_info:
            process_client.publish_workspace_layer(
                WORKSPACE,
                layer_name,
                file_paths=case['file_paths'],
            )

        exc = exc_info.value
        assert exc.code == 2
        assert exc.http_code == 400
        assert exc.data.get('parameter') == 'file'
        assert exc.data.get('expected') == case['expected']
    finally:
        process_client.delete_workspace_layer(WORKSPACE, layer_name, skip_404=True)
