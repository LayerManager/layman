from .filesystem import get_main_file_name


def test_get_main_file_name():
    filenames = [
        'tmp/countries.geojson',
    ]
    assert get_main_file_name(filenames) == 'tmp/countries.geojson'

    filenames = [
        'tmp/countries.zip',
    ]
    assert get_main_file_name(filenames) == None

    filenames = [
        'tmp/countries_lakes.geojson',
        'tmp/countries.geojson',
    ]
    assert get_main_file_name(filenames) == 'tmp/countries_lakes.geojson'

# def test_get_main_file_name():
#     filenames = [
#         'tmp/countries.cpg',
#         'tmp/countries.dbf',
#         'tmp/countries.prj',
#         'tmp/countries.README.html',
#         'tmp/countries.shp',
#         'tmp/countries.shx',
#         'tmp/countries.VERSION.txt',
#     ]
#     assert get_main_file_name(filenames) == 'tmp/countries.shp'
#
#     filenames = [
#         'tmp/countries.cpg',
#         'tmp/countries.dbf',
#         'tmp/countries.prj',
#         'tmp/countries.README.html',
#         'tmp/countries.shx',
#         'tmp/countries.VERSION.txt',
#     ]
#     assert get_main_file_name(filenames) == None
#
#     filenames = [
#         'tmp/countries.cpg',
#         'tmp/countries.dbf',
#         'tmp/countries_lakes.cpg',
#         'tmp/countries_lakes.dbf',
#         'tmp/countries_lakes.prj',
#         'tmp/countries_lakes.README.html',
#         'tmp/countries_lakes.shp',
#         'tmp/countries_lakes.shx',
#         'tmp/countries_lakes.VERSION.txt',
#         'tmp/countries.prj',
#         'tmp/countries.README.html',
#         'tmp/countries.shp',
#         'tmp/countries.shx',
#         'tmp/countries.VERSION.txt',
#     ]
#     assert get_main_file_name(filenames) == 'tmp/countries_lakes.shp'
