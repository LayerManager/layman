import pytest
from layman import app, util as layman_util, settings
from layman.publication_relation import util as pr_util
from test_tools import process_client
from ... import static_data as data
from ..data import ensure_all_publications


@pytest.mark.timeout(600)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman',)
def test_get_publication_infos():
    ensure_all_publications()

    users = data.USERS | {settings.ANONYM_USER, settings.NONAME_USER}
    # prepare expected data
    expected = dict()
    for actor in users:
        expected[actor] = dict()
        for workspace in data.WORKSPACES:
            expected[actor][workspace] = dict()
            for publ_type in process_client.PUBLICATION_TYPES:
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
        headers = data.HEADERS.get(actor)

        # test internal get_publication_infos only with actor and access type
        for access_type in ['read', 'write']:
            with app.app_context():
                publications = layman_util.get_publication_infos(context={'actor_name': actor,
                                                                          'access_type': access_type})
                assert {publ_type for _, publ_type, _ in publications.keys()} == set(process_client.PUBLICATION_TYPES)
                for publ_type in process_client.PUBLICATION_TYPES:
                    for workspace in data.WORKSPACES:
                        publications_set = {name for ws, p_type, name in publications.keys()
                                            if ws == workspace and p_type == publ_type}
                        assert publications_set == expected[actor][workspace][publ_type][access_type]

        for publ_type in process_client.PUBLICATION_TYPES:
            for workspace in data.WORKSPACES:
                # test internal get_publication_infos with workspace, publication type. actor and access type
                for access_type in ['read', 'write']:
                    with app.app_context():
                        publications = layman_util.get_publication_infos(workspace, publ_type, {'actor_name': actor, 'access_type': access_type})
                    assert all(p_workspace == workspace and p_type == publ_type for p_workspace, p_type, _ in publications.keys())
                    publications_set = {name for _, _, name in publications.keys()}
                    assert publications_set == expected[actor][workspace][publ_type][access_type]

                # test authenticated GET Workspace Layers/Maps
                publications = process_client.get_workspace_publications(publ_type, workspace, headers=headers)
                publication_set = {publication['name'] for publication in publications}
                assert publication_set == expected[actor][workspace][publ_type]['read']

            # test authenticated GET Layers/Maps
            publications = process_client.get_publications(publ_type, headers=headers)
            for workspace in data.WORKSPACES:
                publication_set = {publication['name'] for publication in publications
                                   if publication['workspace'] == workspace}
                assert publication_set == expected[actor][workspace][publ_type]['read']


@pytest.mark.timeout(600)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_find_maps_containing_layer():
    ensure_all_publications()

    for l_workspace, l_type, layer in data.LIST_LAYERS:
        expected_maps = {(workspace, publication)
                         for (workspace, publ_type, publication), values in data.PUBLICATIONS.items()
                         if publ_type == data.MAP_TYPE and (l_workspace, l_type, layer) in values[data.TEST_DATA].get('layers', [])}

        with app.app_context():
            result_maps = pr_util.find_maps_containing_layer(l_workspace, layer)
        assert result_maps == expected_maps
