import pytest
from layman import app, util as layman_util
from test_tools import process_client


USERNAME = 'test_delete_user'


@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
def test_delete_user():
    process_client.reserve_username(USERNAME, actor_name=USERNAME)
    publication = 'test_delete_user_publication'
    for publication_type in process_client.PUBLICATION_TYPES:
        process_client.publish_workspace_publication(publication_type, USERNAME, publication, actor_name=USERNAME)

        # check if publications exists
        publications = process_client.get_publications(publication_type, workspace=USERNAME, actor_name=USERNAME)
        assert any(pub.get('name') == publication for pub in publications), f"Publication {publication} was not created"

        # check if publication info exists
        with app.app_context():
            publication_info = layman_util.get_publication_info(USERNAME, publication_type, publication)
        assert isinstance(publication_info, dict) and publication_info, "Publication info cannot be empty"

    # check if workspace exists
    assert workspace_exists(USERNAME), f"Workspace '{USERNAME}' was not found"
    assert user_exists(USERNAME), f"User '{USERNAME}' was not found"

    actor_name = USERNAME
    response = process_client.delete_user(USERNAME, actor_name=actor_name)
    assert response.status_code == 200, response.json()

    # check if publication was deleted
    for publication_type in process_client.PUBLICATION_TYPES:
        publications_after_delete = process_client.get_publications(publication_type, actor_name=USERNAME)
        assert not any(pub.get('name') == publication for pub in publications_after_delete), f"Publication {publications_after_delete} was not deleted"
        # check if publication info was deleted
        with app.app_context():
            publication_info = layman_util.get_publication_info(USERNAME, publication_type, publication)
        assert isinstance(publication_info, dict) and not publication_info, "Publication info should be empty"

    # check if workspace was deleted
    assert not workspace_exists(USERNAME), f"Workspace '{USERNAME}' was not deleted"
    assert not user_exists(USERNAME), f"User '{USERNAME}' was not deleted"


def workspace_exists(workspace):
    with app.app_context():
        return workspace in layman_util.get_workspaces(use_cache=False)


def user_exists(username):
    users = process_client.get_users()
    return any(user.get("username") == username for user in users)
