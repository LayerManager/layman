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
