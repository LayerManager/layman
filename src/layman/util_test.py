from .util import *


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
