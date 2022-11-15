from contextlib import nullcontext as does_not_raise
import pytest
from layman.http import LaymanError

from .input_file import get_all_main_file_names, get_file_name_mappings, slugify_timeseries_filename, \
    is_safe_timeseries_filename, slugify_timeseries_filename_pattern, check_duplicate_mapped_filenames


def test_get_main_file_name():
    filenames = [
        'tmp/countries.geojson',
    ]
    assert get_all_main_file_names(filenames) == ['tmp/countries.geojson']

    filenames = [
        'tmp/countries.zip',
    ]
    assert get_all_main_file_names(filenames) == []

    filenames = [
        'tmp/countries_lakes.geojson',
        'tmp/countries.geojson',
    ]
    assert get_all_main_file_names(filenames) == ['tmp/countries_lakes.geojson', 'tmp/countries.geojson']


def test_get_main_file_name_shp():
    filenames = [
        'tmp/countries.cpg',
        'tmp/countries.dbf',
        'tmp/countries.prj',
        'tmp/countries.README.html',
        'tmp/countries.shp',
        'tmp/countries.shx',
        'tmp/countries.VERSION.txt',
    ]
    assert get_all_main_file_names(filenames) == ['tmp/countries.shp']

    filenames = [
        'tmp/countries.cpg',
        'tmp/countries.dbf',
        'tmp/countries.prj',
        'tmp/countries.README.html',
        'tmp/countries.shx',
        'tmp/countries.VERSION.txt',
    ]
    assert get_all_main_file_names(filenames) == []

    filenames = [
        'tmp/countries.cpg',
        'tmp/countries.dbf',
        'tmp/countries_lakes.cpg',
        'tmp/countries_lakes.dbf',
        'tmp/countries_lakes.prj',
        'tmp/countries_lakes.README.html',
        'tmp/countries_lakes.shp',
        'tmp/countries_lakes.shx',
        'tmp/countries_lakes.VERSION.txt',
        'tmp/countries.prj',
        'tmp/countries.README.html',
        'tmp/countries.shp',
        'tmp/countries.shx',
        'tmp/countries.VERSION.txt',
    ]
    assert get_all_main_file_names(filenames) == ['tmp/countries_lakes.shp', 'tmp/countries.shp', ]


@pytest.mark.parametrize("method_params, exp_filepath_mapping", [
    pytest.param({
        'file_names': [
            'tmp/countries.cpg',
            'tmp/countries.dbf',
            'tmp/countries_lakes.cpg',
            'tmp/countries_lakes.dbf',
            'tmp/countries_lakes.prj',
            'tmp/countries_lakes.README.html',
            'tmp/countries_lakes.shp',
            'tmp/countries_lakes.shx',
            'tmp/countries_lakes.VERSION.txt',
            'tmp/countries.prj',
            'tmp/countries.README.html',
            'tmp/countries.shp',
            'tmp/countries.shx',
            'tmp/countries.VERSION.txt',
        ],
        'main_file_names': ['tmp/countries.shp'],
        'layer_name': 'cntr',
        'output_dir': '/data',
    }, {
        'tmp/countries.cpg': '/data/cntr.cpg',
        'tmp/countries.dbf': '/data/cntr.dbf',
        'tmp/countries.prj': '/data/cntr.prj',
        'tmp/countries.README.html': '/data/cntr.readme.html',
        'tmp/countries.shp': '/data/cntr.shp',
        'tmp/countries.shx': '/data/cntr.shx',
        'tmp/countries.VERSION.txt': '/data/cntr.version.txt',
        'tmp/countries_lakes.cpg': None,
        'tmp/countries_lakes.dbf': None,
        'tmp/countries_lakes.prj': None,
        'tmp/countries_lakes.README.html': None,
        'tmp/countries_lakes.shp': None,
        'tmp/countries_lakes.shx': None,
        'tmp/countries_lakes.VERSION.txt': None,
    }, id='basic'),
    pytest.param({
        'file_names': [
            'compressed.zip/tmp/countries.tif',
            'compressed.zip/tmp/countries.tfw',
            'compressed.zip/tmp/countries2.tif',
            'compressed.zip/tmp/countries2.tfw',
            'compressed.zip/tmp/countries_lakes.cpg',
            'compressed.zip/tmp/countries_lakes.dbf',
            'compressed.zip/tmp/countries_lakes.prj',
            'compressed.zip/tmp/countries_lakes.README.html',
            'compressed.zip/tmp/countries_lakes.shp',
            'compressed.zip/tmp/countries_lakes.shx',
            'compressed.zip/tmp/countries_lakes.VERSION.txt',
            'compressed.zip/tmp/countries.README.html',
            'compressed.zip/tmp/countries.ěščřžýáíéĚŠČŘŽÝÁÍÉ',
        ],
        'main_file_names': ['compressed.zip/tmp/countries.tif', 'compressed.zip/tmp/countries2.tif'],
        'layer_name': 'cntr',
        'output_dir': '/data',
        'name_input_file_by_layer': False,
    }, {
        'compressed.zip/tmp/countries.tif': '/data/countries.tif',
        'compressed.zip/tmp/countries.tfw': '/data/countries.tfw',
        'compressed.zip/tmp/countries2.tif': '/data/countries2.tif',
        'compressed.zip/tmp/countries2.tfw': '/data/countries2.tfw',
        'compressed.zip/tmp/countries.README.html': '/data/countries.README.html',
        'compressed.zip/tmp/countries_lakes.cpg': None,
        'compressed.zip/tmp/countries_lakes.dbf': None,
        'compressed.zip/tmp/countries_lakes.prj': None,
        'compressed.zip/tmp/countries_lakes.README.html': None,
        'compressed.zip/tmp/countries_lakes.shp': None,
        'compressed.zip/tmp/countries_lakes.shx': None,
        'compressed.zip/tmp/countries_lakes.VERSION.txt': None,
        'compressed.zip/tmp/countries.ěščřžýáíéĚŠČŘŽÝÁÍÉ': '/data/countries.escrzyaieESCRZYAIE',
    }, id='not_name_input_file_by_layer'),
])
def test_get_file_name_mappings(method_params, exp_filepath_mapping):
    _, result = get_file_name_mappings(**method_params)
    assert result == exp_filepath_mapping


@pytest.mark.parametrize("method_params, exp_exception", [
    pytest.param({
        'filenames_mapping': {
            'small_layer.geojson': 'small_layer.geojson',
            'small_layer.README.txt': 'small_layer.readme.txt',
        },
    }, None, id='ok'),
    pytest.param({
        'filenames_mapping': {
            'small_layer.geojson': 'small_layer.geojson',
            'small_layer.README.txt': 'small_layer.readme.txt',
            'small_layer.readme.txt': 'small_layer.readme.txt',
        },
    }, {
        'code': 2,
        'parameter': 'file',
        'message': 'Two or more input file names map to the same name.',
        'expected': 'Input file names that differ at least in one letter (ignoring case and diacritics) or number.',
        'similar_filenames_mapping': {
            'small_layer.README.txt': 'small_layer.readme.txt',
            'small_layer.readme.txt': 'small_layer.readme.txt',
        },
    }, id='raises_exception'),
])
def test_check_duplicate_mapped_filenames(method_params, exp_exception):
    expectation = pytest.raises(LaymanError) if exp_exception else does_not_raise()
    with expectation as exc_info:
        check_duplicate_mapped_filenames(**method_params)
    if exp_exception:
        assert exc_info.value.code == exp_exception['code']
        assert exc_info.value.data == {k: v for k, v in exp_exception.items() if k != 'code'}


@pytest.mark.parametrize("filename, exp_result", [
    pytest.param('S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif', 'S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif', id='real_name_S2A'),
    pytest.param('ěščřžýáíéúůóďťň ĚŠČŘŽÝÁÍÉÚŮÓĎŤŇ 2021.TIF', 'escrzyaieuuodtn_ESCRZYAIEUUODTN_2021.TIF', id='czech_diacritics_and_space'),
    pytest.param('áäčďéíĺľňóôŕšťúýž ÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ 2021.TIF', 'aacdeillnoorstuyz_AACDEILLNOORSTUYZ_2021.TIF', id='slovak_diacritics_and_space'),
    pytest.param('ÀàÂâÇçÉéÈèÊêËëÎîÏïÔôÙùÛûÜüŸÿ2021.tif', 'AaAaCcEeEeEeEeIiIiOoUuUuUuYy2021.tif', id='french_diacritics'),
    pytest.param('2022-11-02T10:17:58Z.tif', '2022-11-02T10:17:58Z.tif', id='time_with_colons'),
    pytest.param('ßÆ.tif', 'ßÆ.tif', id='unsupported_latin_ligatures'),
])
def test_slugify_timeseries_filename(filename, exp_result):
    assert slugify_timeseries_filename(filename) == exp_result


@pytest.mark.parametrize("pattern, exp_result", [
    pytest.param(r"[0-9]{8}", r"[0-9]{8}", id='date'),
    pytest.param(r"[0-9]{8}T[0-9]{9}Z", r"[0-9]{8}T[0-9]{9}Z", id='iso8601'),
    pytest.param(r".*([0-9]{8}T[0-9]{9}Z).*", r".*([0-9]{8}T[0-9]{9}Z).*", id='group'),
    pytest.param(r"^Jihočeský kraj ([0-9]{8}).*$", r"^Jihocesky_kraj_([0-9]{8}).*$", id='czech_diacritics_and_space'),
])
def test_slugify_timeseries_filename_pattern(pattern, exp_result):
    assert slugify_timeseries_filename_pattern(pattern) == exp_result


@pytest.mark.parametrize("filename, exp_result", [
    pytest.param('S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif', True, id='real_name_S2A'),
    pytest.param('2022-11-02T120157.123.tif', True, id='iso8601_time_without_colons'),
    pytest.param('2022-11-02T12:01:57.123.tif', False, id='iso8601_time_with_colons'),
    pytest.param('.abc.tif', False, id='starts_with_dot'),
])
def test_is_safe_timeseries_filename(filename, exp_result):
    assert is_safe_timeseries_filename(filename) == exp_result
