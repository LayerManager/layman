from .input_file import get_all_main_file_names, get_file_name_mappings


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


def test_get_file_name_mappings():
    cfg = {
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
        'output_dir': '/data'
    }
    assert get_file_name_mappings(**cfg)[1] == {
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
    }
