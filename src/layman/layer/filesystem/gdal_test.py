import os
from contextlib import nullcontext as does_not_raise
from osgeo import gdalconst
import pytest

from layman import LaymanError
from test_tools import util as test_util
from . import gdal


@pytest.mark.parametrize('file_path, exp_error', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', None),
    ('sample/layman.layer/sample_tif_rgb.tif', None),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', None),
    ('sample/layman.layer/sample_tif_rgba.tif', None),
    ('sample/layman.layer/sample_tiff_rgba_opaque.tiff', None),
    ('sample/layman.layer/sample_tif_tfw_rgba_opaque.tif', None),
    ('sample/layman.layer/sample_tif_colortable_nodata_opaque.tif', None),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', None),
    ('sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif', None),
    ('sample/layman.layer/sample_jpg_aux_rgba.jpg', None),
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
    ('sample/layman.layer/sample_tiff_rgba_opaque.tiff', [None, None, None, None]),
    ('sample/layman.layer/sample_tif_tfw_rgba_opaque.tif', [None, None, None, None]),
    ('sample/layman.layer/sample_tif_colortable_nodata_opaque.tif', [255]),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', [3.402823466e+38, 3.402823466e+38]),
    ('sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif', [3.402823466e+38]),
    ('sample/layman.layer/sample_tif_rg.tif', [None, None]),
    ('sample/layman.layer/sample_jpg_aux_rgba.jpg', [None, None, None]),
])
def test_get_nodata_values(file_path, exp_result):
    assert gdal.get_nodata_values(file_path) == exp_result


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', [15.301769911504218, -15.303030303030303]),
    ('sample/layman.layer/sample_tif_rgb.tif', [0.04373913043462064, -0.04374999999923662]),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', [0.04373913043462064, -0.04374999999923662]),
    ('sample/layman.layer/sample_tif_rgba.tif', [0.04373913043462064, -0.04374999999923662]),
    ('sample/layman.layer/sample_tiff_rgba_opaque.tiff', [14.716791979949875, -14.733496332518337]),
    ('sample/layman.layer/sample_tif_tfw_rgba_opaque.tif', [14.7167919799, -14.7334963325]),
    ('sample/layman.layer/sample_tif_colortable_nodata_opaque.tif', [92.930501930501933, -92.976470588235287]),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', [15.293650793650794, -15.308571428571428]),
    ('sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif', [15.293650793650794, -15.308571428571428]),
    ('sample/layman.layer/sample_tif_rg.tif', [0.04373913043462064, -0.04374999999923662]),
])
def test_get_pixel_size(file_path, exp_result):
    assert gdal.get_pixel_size(file_path) == exp_result


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', [[17, 255], [30, 255], [16, 255]]),  # [min, max] for each band
    ('sample/layman.layer/sample_tif_rgb.tif', [[0, 251], [0, 253], [0, 254]]),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', [[33, 251], [57, 253], [1, 254]]),
    ('sample/layman.layer/sample_tif_rgba.tif', [[0, 251], [0, 253], [0, 254], [0, 127]]),
    ('sample/layman.layer/sample_tiff_rgba_opaque.tiff', [[0, 254], [0, 222], [0, 216], [255, 255]]),
    ('sample/layman.layer/sample_tif_tfw_rgba_opaque.tif', [[0, 254], [0, 222], [0, 216], [255, 255]]),
    ('sample/layman.layer/sample_tif_colortable_nodata_opaque.tif', [[0, 20]]),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', [[-0.0094339624047279, 0.91247737407684], [0, 255]]),
    ('sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif', [[-0.040201004594564, 0.91754120588303]]),
    ('sample/layman.layer/sample_tif_rg.tif', [[0, 251], [0, 253]]),
])
def test_get_statistics(file_path, exp_result):
    stats = gdal.get_statistics(file_path)
    assert len(stats) == len(exp_result), stats
    for band_idx, exp_band_stats in enumerate(exp_result):
        assert all((stats[band_idx][i] - exp_band_stats[i]) <= 0.00000000000001
                   for i in range(0, len(exp_band_stats))), f"band_idx={band_idx}, stats={stats[band_idx]}"


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', False),  # no alpha, no nodata
    ('sample/layman.layer/sample_tif_rgb.tif', False),  # no alpha, no nodata
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', True),  # no alpha, min <= nodata <= max
    ('sample/layman.layer/sample_tif_rgba.tif', True),  # alpha with at least one value < 255
    ('sample/layman.layer/sample_tiff_rgba_opaque.tiff', False),  # alpha with all values = 255, no nodata
    ('sample/layman.layer/sample_tif_tfw_rgba_opaque.tif', False),  # alpha with all values = 255, no nodata
    ('sample/layman.layer/sample_tif_colortable_nodata_opaque.tif', False),  # no alpha, nodata > max in each band
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', True),  # alpha with at least one value < 255
    ('sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif', False),  # no alpha, nodata > max in each band
    ('sample/layman.layer/sample_tif_rg.tif', False),  # no alpha, no nodata
    ('sample/layman.layer/sample_jpg_aux_rgba.jpg', True),  # no alpha, no nodata
])
def test_is_normalized_alpha_needed(file_path, exp_result):
    color_interp = gdal.get_color_interpretations(file_path)
    nodata_values = gdal.get_nodata_values(file_path)
    assert gdal.is_normalized_alpha_needed(file_path, color_interp=color_interp, nodata_values=nodata_values) == exp_result


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', [{gdalconst.GMF_ALL_VALID}] * 3),
    ('sample/layman.layer/sample_tif_rgb.tif', [{gdalconst.GMF_ALL_VALID}] * 3),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', [{gdalconst.GMF_NODATA}] * 3),
    ('sample/layman.layer/sample_tif_rgba.tif',
     [{gdalconst.GMF_PER_DATASET, gdalconst.GMF_ALPHA}] * 3 + [{gdalconst.GMF_ALL_VALID}]),
    ('sample/layman.layer/sample_tiff_rgba_opaque.tiff',
     [{gdalconst.GMF_PER_DATASET, gdalconst.GMF_ALPHA}] * 3 + [{gdalconst.GMF_ALL_VALID}]),
    ('sample/layman.layer/sample_tif_tfw_rgba_opaque.tif',
     [{gdalconst.GMF_PER_DATASET, gdalconst.GMF_ALPHA}] * 3 + [{gdalconst.GMF_ALL_VALID}]),
    ('sample/layman.layer/sample_tif_colortable_nodata_opaque.tif', [{gdalconst.GMF_NODATA}]),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', [{gdalconst.GMF_NODATA}] * 2),
    ('sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif', [{gdalconst.GMF_NODATA}]),
    ('sample/layman.layer/sample_jpg_aux_rgba.jpg', [{gdalconst.GMF_PER_DATASET}] * 3),
])
def test_get_mask_flags(file_path, exp_result):
    mask_flags = gdal.get_mask_flags(file_path)
    assert mask_flags == exp_result


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', False),
    ('sample/layman.layer/sample_tif_rgb.tif', False),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', False),
    ('sample/layman.layer/sample_tif_rgba.tif', False),
    ('sample/layman.layer/sample_tiff_rgba_opaque.tiff', False),
    ('sample/layman.layer/sample_tif_tfw_rgba_opaque.tif', False),
    ('sample/layman.layer/sample_tif_colortable_nodata_opaque.tif', True),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', True),
    ('sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif', True),
    ('sample/layman.layer/sample_tif_rg.tif', False),
])
def test_is_nodata_out_of_min_max(file_path, exp_result):
    nodata_values = gdal.get_nodata_values(file_path)
    assert gdal.is_nodata_out_of_min_max(file_path, nodata_values=nodata_values) == exp_result


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', None),
    ('sample/layman.layer/sample_tif_rgb.tif', None),
    ('sample/layman.layer/sample_tif_rgb_nodata.tif', None),
    ('sample/layman.layer/sample_tif_rgba.tif', None),
    ('sample/layman.layer/sample_tiff_rgba_opaque.tiff', 'sample/layman.layer/sample_tiff_rgba_opaque.vrt'),
    ('sample/layman.layer/sample_tif_tfw_rgba_opaque.tif', 'sample/layman.layer/sample_tif_tfw_rgba_opaque.vrt'),
    ('sample/layman.layer/sample_tif_colortable_nodata_opaque.tif', None),
    ('sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif', None),
    ('sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif', None),
])
def test_create_vrt_file_if_needed(file_path, exp_result):
    if exp_result:
        assert not os.path.exists(exp_result)
    result = gdal.create_vrt_file_if_needed(file_path)
    assert result == exp_result
    if result:
        assert os.path.exists(exp_result)
        os.remove(exp_result)


@pytest.mark.parametrize('file_path, exp_result', [
    ('sample/layman.layer/sample_jp2_rgb.jp2', 'JP2OpenJPEG'),
    ('sample/layman.layer/sample_tif_rgb.tif', 'GTiff'),
    ('sample/layman.layer/sample_tiff_rgba_opaque.tiff', 'GTiff'),
    ('sample/layman.layer/sample_jpg_aux_rgba.jpg', 'JPEG'),
])
def test_get_driver_short_name(file_path, exp_result):
    assert gdal.get_driver_short_name(file_path) == exp_result
