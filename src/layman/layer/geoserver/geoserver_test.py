from . import get_layman_rules, get_non_layman_workspaces


def test_get_layman_rules():
    layman_role = 'LAYMAN_ROLE'
    all_rules = {
        "*.*.r": "*",
        "*.*.w": "GROUP_ADMIN,ADMIN",
    }
    assert get_layman_rules(all_rules, layman_role) == {}

    all_rules = {
        "*.*.w": "GROUP_ADMIN,LAYMAN_ROLE,ADMIN",
        "*.*.r": "*",
        "acme.*.w": "ADMIN,LAYMAN_ROLE",
        "acme2.*.r": "LAYMAN_ROLE",
        "acme2.*.w": "LAYMAN_ROLE,ADMIN",
    }
    assert get_layman_rules(all_rules, layman_role) == {
        "*.*.w": "GROUP_ADMIN,LAYMAN_ROLE,ADMIN",
        "acme.*.w": "ADMIN,LAYMAN_ROLE",
        "acme2.*.r": "LAYMAN_ROLE",
        "acme2.*.w": "LAYMAN_ROLE,ADMIN",
    }


def test_get_non_layman_workspaces():
    layman_rules = {
        "*.*.w": "GROUP_ADMIN,LAYMAN_ROLE,ADMIN",
        "acme.*.w": "ADMIN,LAYMAN_ROLE",
    }
    all_workspaces = [
        {
            "name": "acme",
            "href": r"http:\/\/geoserver:8080\/geoserver\/rest\/workspaces\/acme.json"
        },
        {
            "name": "acme2",
            "href": r"http:\/\/geoserver:8080\/geoserver\/rest\/workspaces\/acme2.json"
        },
    ]
    assert get_non_layman_workspaces(all_workspaces, layman_rules) == [
        {
            "name": "acme2",
            "href": r"http:\/\/geoserver:8080\/geoserver\/rest\/workspaces\/acme2.json"
        },
    ]
    layman_rules = {}
    assert get_non_layman_workspaces(all_workspaces, layman_rules) == all_workspaces
