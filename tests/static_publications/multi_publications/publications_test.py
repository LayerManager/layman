import pytest
from layman import app, util as layman_util, settings
from layman.common.prime_db_schema import publications
from layman.publication_relation import util as pr_util
from test_tools import process_client
from ... import static_publications as data
from ..data import ensure_all_publications


@pytest.mark.timeout(600)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman',)
def test_get_publication_infos():
    ensure_all_publications()

    users = data.USERS | {settings.ANONYM_USER, settings.NONAME_USER}
    expected = dict()
    for actor in users:
        expected[actor] = dict()
        for workspace in data.WORKSPACES:
            expected[actor][workspace] = dict()
            for publ_type in [process_client.LAYER_TYPE, process_client.MAP_TYPE]:
                expected[actor][workspace][publ_type] = dict()
                for access_type in ['read', 'write']:
                    expected[actor][workspace][publ_type][access_type] = set()

    for (workspace, publ_type, publication), value in data.PUBLICATIONS.items():
        for access_type in ['read', 'write']:
            users_with_right = value[data.TEST_DATA].get('users_can_' + access_type)
            users_with_right = users_with_right or users
            for actor in users_with_right:
                expected[actor][workspace][publ_type][access_type].add(publication)

    for actor in users:
        for workspace in data.WORKSPACES:
            for publ_type in [process_client.LAYER_TYPE, process_client.MAP_TYPE]:
                for access_type in ['read', 'write']:
                    with app.app_context():
                        publications = layman_util.get_publication_infos(workspace, publ_type, {'actor_name': actor, 'access_type': access_type})
                    assert all(p_workspace == workspace and p_type == publ_type for p_workspace, p_type, _ in publications.keys())
                    publications_set = {name for _, _, name in publications.keys()}
                    assert publications_set == expected[actor][workspace][publ_type][access_type]

                headers = data.HEADERS.get(actor)
                publications = process_client.get_workspace_publications(publ_type, workspace, headers=headers)
                publication_set = {publication['name'] for publication in publications}
                assert publication_set == expected[actor][workspace][publ_type]['read']


@pytest.mark.timeout(600)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_publications_same_name():
    ensure_all_publications()

    for workspace in data.WORKSPACES:
        exp_pubs = [(wspace, ptype, publication) for wspace, ptype, publication in data.PUBLICATIONS
                    if wspace == workspace]
        with app.app_context():
            pubs = publications.get_publication_infos(workspace)
        assert len(pubs) == len(exp_pubs)
        for key in exp_pubs:
            assert key in pubs

    with app.app_context():
        pubs = publications.get_publication_infos()
    assert len(pubs) == len(data.PUBLICATIONS)
    assert set(data.PUBLICATIONS) == set(pubs)


@pytest.mark.timeout(600)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_find_maps_containing_layer():
    ensure_all_publications()

    for l_workspace, l_type, layer in data.LIST_LAYERS:
        expected_maps = {(workspace, publication)
                         for (workspace, publ_type, publication), values in data.PUBLICATIONS.items()
                         if publ_type == data.MAP_TYPE and (l_workspace, l_type, layer) in values[data.TEST_DATA].get('layers', list())}

        with app.app_context():
            result_maps = pr_util.find_maps_containing_layer(l_workspace, layer)
        assert result_maps == expected_maps
