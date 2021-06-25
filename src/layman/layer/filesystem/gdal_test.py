from contextlib import nullcontext as does_not_raise
from test import util as test_util
import pytest
from layman import LaymanError
from . import gdal


@pytest.mark.parametrize('file_path, exp_error', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', None),
    ('sample/layman.layer/sample_tif_rgb.tif', None),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', None),
    ('sample/layman.layer/sample_tif_rgba.tif', None),
    ('sample/layman.layer/sample_tiff_rgba.tiff', None),
    ('sample/layman.layer/sample_tif_tfw_rgba.tif', None),
    ('sample/layman.layer/sample_tif_colortable_nodata.tif', None),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', None),
    ('sample/layman.layer/sample_tif_grayscale_nodata.tif', None),
    ('sample/layman.layer/sample_tif_rg.tif', {'http_code': 400,
                                               'code': 2,
                                               'detail': {'parameter': 'file',
                                                          'expected': 'Any of color interpretations [Gray], '
                                                                      '[Gray, Alpha], [Palette], [Red, Green, Blue], '
                                                                      '[Red, Green, Blue, Alpha].',
                                                          'found': ['Red', 'Green']
                                                          },
                                               }),
])
def test_assert_valid_raster(file_path, exp_error):
    exp_exception = pytest.raises(LaymanError) if exp_error else does_not_raise()

    with exp_exception as exc_info:
        gdal.assert_valid_raster(file_path)

    if exp_error:
        test_util.assert_error(exp_error, exc_info)


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', [None, None, None]),
    ('sample/layman.layer/sample_tif_rgb.tif', [None, None, None]),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', [0, 0, 0]),
    ('sample/layman.layer/sample_tif_rgba.tif', [None, None, None, None]),
    ('sample/layman.layer/sample_tiff_rgba.tiff', [None, None, None, None]),
    ('sample/layman.layer/sample_tif_tfw_rgba.tif', [None, None, None, None]),
    ('sample/layman.layer/sample_tif_colortable_nodata.tif', [255]),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', [3.402823466e+38, 3.402823466e+38]),
    ('sample/layman.layer/sample_tif_grayscale_nodata.tif', [3.402823466e+38]),
    ('sample/layman.layer/sample_tif_rg.tif', [None, None]),
])
def test_get_nodata_values(file_path, exp_result):
    assert gdal.get_nodata_values(file_path) == exp_result


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', [15.301769911504218, -15.303030303030303]),
    ('sample/layman.layer/sample_tif_rgb.tif', [0.04373913043462064, -0.04374999999923662]),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', [0.04373913043462064, -0.04374999999923662]),
    ('sample/layman.layer/sample_tif_rgba.tif', [0.04373913043462064, -0.04374999999923662]),
    ('sample/layman.layer/sample_tiff_rgba.tiff', [14.716791979949875, -14.733496332518337]),
    ('sample/layman.layer/sample_tif_tfw_rgba.tif', [14.716791979949875, -14.733496332518337]),
    ('sample/layman.layer/sample_tif_colortable_nodata.tif', [92.930501930501933, -92.976470588235287]),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', [15.293650793650794, -15.308571428571428]),
    ('sample/layman.layer/sample_tif_grayscale_nodata.tif', [15.293650793650794, -15.308571428571428]),
    ('sample/layman.layer/sample_tif_rg.tif', [0.04373913043462064, -0.04374999999923662]),
])
def test_get_pixel_size(file_path, exp_result):
    assert gdal.get_pixel_size(file_path) == exp_result


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', [[17, 255], [30, 255], [16, 255]]),  # [min, max] for each band
    ('sample/layman.layer/sample_tif_rgb.tif', [[0, 251], [0, 253], [0, 254]]),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', [[33, 251], [57, 253], [1, 254]]),
    ('sample/layman.layer/sample_tif_rgba.tif', [[0, 251], [0, 253], [0, 254], [0, 127]]),
    ('sample/layman.layer/sample_tiff_rgba.tiff', [[0, 254], [0, 222], [0, 216], [255, 255]]),
    ('sample/layman.layer/sample_tif_tfw_rgba.tif', [[0, 254], [0, 222], [0, 216], [255, 255]]),
    ('sample/layman.layer/sample_tif_colortable_nodata.tif', [[0, 20]]),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', [[-0.0094339624047279, 0.91247737407684], [0, 255]]),
    ('sample/layman.layer/sample_tif_grayscale_nodata.tif', [[-0.040201004594564, 0.91754120588303]]),
    ('sample/layman.layer/sample_tif_rg.tif', [[0, 251], [0, 253]]),
])
def test_get_statistics(file_path, exp_result):
    stats = gdal.get_statistics(file_path)
    assert len(stats) == len(exp_result), stats
    for band_idx, exp_band_stats in enumerate(exp_result):
        assert stats[band_idx][:len(exp_band_stats)] == exp_band_stats
