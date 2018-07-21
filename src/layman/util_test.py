from .util import *
from .settings import *

def test_slugify():
    assert slugify('Brno-město') == 'brno_mesto'
    assert slugify('Brno__město') == 'brno_mesto'
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
#
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
        'main_file_name': 'tmp/countries.shp',
        'layer_name': 'cntr',
        'user_dir': '/data'
    }
    assert get_file_name_mappings(**cfg)[1] == {
        'tmp/countries.cpg': '/data/cntr.cpg',
        'tmp/countries.dbf': '/data/cntr.dbf',
        'tmp/countries.prj': '/data/cntr.prj',
        'tmp/countries.README.html': '/data/cntr.README.html',
        'tmp/countries.shp': '/data/cntr.shp',
        'tmp/countries.shx': '/data/cntr.shx',
        'tmp/countries.VERSION.txt': '/data/cntr.VERSION.txt',
        'tmp/countries_lakes.cpg': None,
        'tmp/countries_lakes.dbf': None,
        'tmp/countries_lakes.prj': None,
        'tmp/countries_lakes.README.html': None,
        'tmp/countries_lakes.shp': None,
        'tmp/countries_lakes.shx': None,
        'tmp/countries_lakes.VERSION.txt': None,
    }

def test_get_layman_rules():
    layman_role='LAYMAN_ROLE'
    all_rules = {
        "*.*.r":"*",
        "*.*.w":"GROUP_ADMIN,ADMIN",
    }
    assert get_layman_rules(all_rules,layman_role) == {}

    all_rules = {
        "*.*.w":"GROUP_ADMIN,LAYMAN_ROLE,ADMIN",
        "*.*.r":"*",
        "acme.*.w":"ADMIN,LAYMAN_ROLE",
        "acme2.*.r":"LAYMAN_ROLE",
        "acme2.*.w":"LAYMAN_ROLE,ADMIN",
    }
    assert get_layman_rules(all_rules,layman_role) == {
        "*.*.w":"GROUP_ADMIN,LAYMAN_ROLE,ADMIN",
        "acme.*.w":"ADMIN,LAYMAN_ROLE",
        "acme2.*.r":"LAYMAN_ROLE",
        "acme2.*.w":"LAYMAN_ROLE,ADMIN",
    }


def test_get_non_layman_workspaces():
    layman_rules = {
        "*.*.w":"GROUP_ADMIN,LAYMAN_ROLE,ADMIN",
        "acme.*.w":"ADMIN,LAYMAN_ROLE",
    }
    all_workspaces = [
        {
            "name":"acme",
            "href":"http:\/\/geoserver:8080\/geoserver\/rest\/workspaces\/acme.json"
        },
        {
            "name":"acme2",
            "href":"http:\/\/geoserver:8080\/geoserver\/rest\/workspaces\/acme2.json"
        },
    ]
    assert get_non_layman_workspaces(all_workspaces, layman_rules) == [
        {
            "name":"acme2",
            "href":"http:\/\/geoserver:8080\/geoserver\/rest\/workspaces\/acme2.json"
        },
    ]
    layman_rules = {}
    assert get_non_layman_workspaces(all_workspaces, layman_rules) == all_workspaces
