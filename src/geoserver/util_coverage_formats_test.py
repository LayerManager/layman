from geoserver.util import (
    COVERAGE_SUPPORTED_FORMATS,
    _merge_coverage_supported_formats,
    _normalize_coverage_supported_formats,
)


def test_normalize_coverage_supported_formats():
    assert _normalize_coverage_supported_formats({}) == []
    assert _normalize_coverage_supported_formats({'supportedFormats': None}) == []
    assert _normalize_coverage_supported_formats({'supportedFormats': ''}) == []
    assert _normalize_coverage_supported_formats({'supportedFormats': {'string': 'GEOTIFF'}}) == ['GEOTIFF']
    assert _normalize_coverage_supported_formats({
        'supportedFormats': {'string': ['GEOTIFF', 'PNG']},
    }) == ['GEOTIFF', 'PNG']
    assert _normalize_coverage_supported_formats({
        'supportedFormats': ['JPEG', 'TIFF'],
    }) == ['JPEG', 'TIFF']


def test_merge_coverage_supported_formats_preserves_extras():
    merged = _merge_coverage_supported_formats(['ArcGrid', 'GEOTIFF'])
    assert merged[0] == 'ArcGrid'
    assert 'GEOTIFF' in merged
    assert set(COVERAGE_SUPPORTED_FORMATS).issubset(merged)
    assert merged == _merge_coverage_supported_formats(merged)


def test_coverage_supported_formats_constant():
    assert 'GEOTIFF' in COVERAGE_SUPPORTED_FORMATS
    assert set(COVERAGE_SUPPORTED_FORMATS) == {'GEOTIFF', 'PNG', 'JPEG', 'TIFF'}
