from .util import slugify, to_safe_layer_name, get_main_file_name

def test_slugify():
    assert slugify('Brno-město') == 'brno_mesto'
    assert slugify(' ') == ''
    assert slugify(' ?:"+  @') == ''
    assert slugify('01 Stanice vodních toků 26.4.2017 (voda)') == \
           '01_stanice_vodnich_toku_26_4_2017_voda'

def test_to_safe_layer_name():
    assert to_safe_layer_name('') == 'layer'
    assert to_safe_layer_name(' ?:"+  @') == 'layer'
    assert to_safe_layer_name('01 Stanice vodních toků 26.4.2017 (voda)') == \
           'layer_01_stanice_vodnich_toku_26_4_2017_voda'

def test_get_main_file_name():
    filenames = [
        'tmp/countries.cpg',
        'tmp/countries.dbf',
        'tmp/countries.prj',
        'tmp/countries.README.html',
        'tmp/countries.shp',
        'tmp/countries.shx',
        'tmp/countries.VERSION.txt',
    ]
    assert get_main_file_name(filenames) == 'tmp/countries.shp'

    filenames = [
        'tmp/countries.cpg',
        'tmp/countries.dbf',
        'tmp/countries.prj',
        'tmp/countries.README.html',
        'tmp/countries.shx',
        'tmp/countries.VERSION.txt',
    ]
    assert get_main_file_name(filenames) == None

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
    assert get_main_file_name(filenames) == 'tmp/countries_lakes.shp'

