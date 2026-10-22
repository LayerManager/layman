from geoserver.util import (
    COVERAGE_SUPPORTED_FORMATS,
    merge_coverage_srs,
    merge_coverage_supported_formats,
    normalize_coverage_srs,
    normalize_coverage_supported_formats,
)
from layman import settings


def test_normalize_coverage_supported_formats():
    assert normalize_coverage_supported_formats({}) == []
    assert normalize_coverage_supported_formats({'supportedFormats': None}) == []
    assert normalize_coverage_supported_formats({'supportedFormats': ''}) == []
    assert normalize_coverage_supported_formats({'supportedFormats': {'string': 'GEOTIFF'}}) == ['GEOTIFF']
    assert normalize_coverage_supported_formats({
        'supportedFormats': {'string': ['GEOTIFF', 'PNG']},
    }) == ['GEOTIFF', 'PNG']
    assert normalize_coverage_supported_formats({
        'supportedFormats': ['JPEG', 'TIFF'],
    }) == ['JPEG', 'TIFF']


def test_merge_coverage_supported_formats_preserves_extras():
    merged = merge_coverage_supported_formats(['ArcGrid', 'GEOTIFF'])
    assert merged[0] == 'ArcGrid'
    assert 'GEOTIFF' in merged
    assert set(COVERAGE_SUPPORTED_FORMATS).issubset(merged)
    assert merged == merge_coverage_supported_formats(merged)


def test_coverage_supported_formats_constant():
    assert 'GEOTIFF' in COVERAGE_SUPPORTED_FORMATS
    assert set(COVERAGE_SUPPORTED_FORMATS) == {'GEOTIFF', 'PNG', 'JPEG', 'TIFF'}


def test_merge_coverage_srs_preserves_extras():
    extra_crs = 'EPSG:3006'
    native_crs = 'EPSG:3857'
    coverage = {'requestSRS': {'string': [extra_crs, native_crs, extra_crs]}}
    existing = normalize_coverage_srs(coverage, 'requestSRS')
    merged = merge_coverage_srs(existing, [native_crs, *settings.LAYMAN_OUTPUT_SRS_LIST])
    assert merged[0] == extra_crs
    assert native_crs in merged
    assert set(settings.LAYMAN_OUTPUT_SRS_LIST).issubset(merged)
    assert len(merged) == len(set(merged))
    assert merged == merge_coverage_srs(merged, [native_crs, *settings.LAYMAN_OUTPUT_SRS_LIST])
