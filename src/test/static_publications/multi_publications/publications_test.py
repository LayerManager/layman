import pytest
from layman import app, util as layman_util, settings
from test_tools import process_client
from ... import static_publications as data
from ..data import ensure_all_publications


@pytest.mark.timeout(600)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman',)
def test_get_publication_infos():
    ensure_all_publications()

    users = data.USERS | {settings.ANONYM_USER, settings.NONAME_USER}
    expected = dict()
    for user in users:
        expected[user] = dict()
        for workspace in data.WORKSPACES:
            expected[user][workspace] = dict()
            for publ_type in [process_client.LAYER_TYPE, process_client.MAP_TYPE]:
                expected[user][workspace][publ_type] = dict()
                for access_type in ['read', 'write']:
                    expected[user][workspace][publ_type][access_type] = set()

    for (workspace, publ_type, publication), value in data.PUBLICATIONS.items():
        for access_type in ['read', 'write']:
            users_with_right = value[data.TEST_DATA].get('users_can_' + access_type)
            users_with_right = users_with_right or users
            for user in users_with_right:
                expected[user][workspace][publ_type][access_type].add(publication)

    for user in users:
        for workspace in data.WORKSPACES:
            for publ_type in [process_client.LAYER_TYPE, process_client.MAP_TYPE]:
                for access_type in ['read', 'write']:
                    with app.app_context():
                        publications = layman_util.get_publication_infos(workspace, publ_type, {'actor_name': user, 'access_type': access_type})
                    assert all(p_workspace == workspace and p_type == publ_type for p_workspace, p_type, _ in publications.keys())
                    publications_set = {name for _, _, name in publications.keys()}
                    assert publications_set == expected[user][workspace][publ_type][access_type]

                headers = data.HEADERS.get(user)
                publications = process_client.get_workspace_publications(publ_type, workspace, headers=headers)
                publication_set = {publication['name'] for publication in publications}
                assert publication_set == expected[user][workspace][publ_type]['read']
