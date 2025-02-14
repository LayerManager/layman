import pytest
from layman import app, util as layman_util
from layman.http import LaymanError
from layman_settings import ANONYM_USER, NONAME_USER
from test_tools import process_client, role_service, process


@pytest.fixture(scope='module')
def _setup_env_vars():
    env_vars = dict(process.AUTHN_SETTINGS)
    env_vars['GRANT_DELETE_OTHER_USER'] = "test_delete_user2,ADMIN"
    process.ensure_layman_function(env_vars)
    yield
    role_service.delete_role('ADMIN')


@pytest.fixture(scope='function')
def setup_users_and_role(request, _setup_env_vars):
    username, actor_name, rolename = request.param
    process_client.reserve_username(username, actor_name=username)
    if actor_name != username:
        process_client.ensure_reserved_username(actor_name)
    if rolename:
        role_service.ensure_user_role(actor_name, rolename)
    yield username, actor_name, rolename
    if actor_name != username:
        process_client.delete_user(actor_name, actor_name=actor_name)


@pytest.fixture(scope='function')
def setup_users_for_testing_errors(request):
    username, actor_name, expected_status, exp_layman_code = request.param
    if expected_status == 403:
        process_client.reserve_username(username, actor_name=username)
    process_client.ensure_reserved_username(actor_name)
    yield username, actor_name, expected_status, exp_layman_code
    if actor_name != username:
        process_client.delete_user(actor_name, actor_name=actor_name)


@pytest.mark.parametrize('setup_users_and_role', [
    ("test_delete_user", "test_delete_user", None),
    ("test_delete_user", "test_delete_user2", None),
    ("test_delete_user", "test_delete_user2", "ADMIN"),
], indirect=True)
@pytest.mark.usefixtures('oauth2_provider_mock')
def test_delete_user(setup_users_and_role):
    username, actor_name, _ = setup_users_and_role
    publication = 'test_delete_user_publication'
    for publication_type in process_client.PUBLICATION_TYPES:
        process_client.publish_workspace_publication(publication_type, username, publication, actor_name=username)

        # check if publications exists
        publications = process_client.get_publications(publication_type, workspace=username, actor_name=username)
        assert any(pub.get('name') == publication for pub in publications), f"Publication {publication} was not created"

        # check if publication info exists
        with app.app_context():
            publication_info = layman_util.get_publication_info(username, publication_type, publication)
        assert isinstance(publication_info, dict) and publication_info, "Publication info cannot be empty"

    # check if workspace exists
    assert workspace_exists(username), f"Workspace '{username}' was not found"
    # check if user exists
    assert user_exists(username), f"User '{username}' was not found"

    response = process_client.delete_user(username, actor_name=actor_name)
    assert response.status_code == 200, response.json()

    # check if publication was deleted
    for publication_type in process_client.PUBLICATION_TYPES:
        publications_after_delete = process_client.get_publications(publication_type, actor_name=username)
        assert not any(pub.get('name') == publication for pub in publications_after_delete), f"Publication {publications_after_delete} was not deleted"
        # check if publication info was deleted
        with app.app_context():
            publication_info = layman_util.get_publication_info(username, publication_type, publication)
        assert isinstance(publication_info, dict) and not publication_info, "Publication info should be empty"

    # check if workspace was deleted
    assert not workspace_exists(username), f"Workspace '{username}' was not deleted"
    # check if user was deleted
    assert not user_exists(username), f"User '{username}' was not deleted"


@pytest.mark.parametrize('setup_users_for_testing_errors', [
    ('non_existing_user', 'test_delete_user_negative2', 404, 57),
    ('test_delete_user_negative', 'test_delete_user_negative2', 403, 30),
    ('', 'test_delete_user_negative2', 404, None),
    (ANONYM_USER, 'test_delete_user_negative2', 404, 57),
    (NONAME_USER, 'test_delete_user_negative2', 404, 57),
], indirect=True)
@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
def test_delete_user_negative(setup_users_for_testing_errors):
    username, actor_name, expected_status, exp_layman_code = setup_users_for_testing_errors
    if exp_layman_code is None:
        # check only status code for empty string layername
        response = process_client.delete_user(username, actor_name=actor_name)
        assert response.status_code == expected_status
    else:
        with pytest.raises(LaymanError) as exc_info:
            process_client.delete_user(username, actor_name=actor_name)
        assert exc_info.value.code == exp_layman_code
        assert exc_info.value.http_code == expected_status


def workspace_exists(workspace):
    with app.app_context():
        return workspace in layman_util.get_workspaces(use_cache=False)


def user_exists(username):
    users = process_client.get_users()
    return any(user.get("username") == username for user in users)
