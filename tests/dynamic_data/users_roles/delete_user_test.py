import pytest
from layman import app, util as layman_util
from layman.http import LaymanError
from layman_settings import ANONYM_USER, NONAME_USER, RIGHTS_EVERYONE_ROLE
from test_tools import process_client, role_service, process, external_db


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


@pytest.fixture(scope='function')
def setup_user_or_everyone(request):
    username, reader, test_delete_user_publication_reader = request.param
    users = process_client.get_users()
    if not any(user['username'] == username for user in users):
        process_client.reserve_username(username, actor_name=username)
    if reader != RIGHTS_EVERYONE_ROLE and not any(user['username'] == reader for user in users):
        process_client.reserve_username(reader, actor_name=reader)
    yield username, reader, test_delete_user_publication_reader


@pytest.fixture
def _setup_role(request):
    rolename = request.param
    if rolename:
        with app.app_context():
            role_service.ensure_role(rolename)
    yield rolename
    if rolename:
        with app.app_context():
            role_service.delete_role(rolename)


@pytest.mark.parametrize('setup_users_and_role', [
    pytest.param(("test_delete_user", "test_delete_user", None), id="self_delete"),
    pytest.param(("test_delete_user", "test_delete_user2", None), id="different_actor"),
    pytest.param(("test_delete_user", "test_delete_user2", "ADMIN"), id="actor_with_role"),
], indirect=True)
@pytest.mark.parametrize('workspace', [
    pytest.param(lambda username: f"{username}", id="user_workspace"),
    pytest.param("public_workspace", id="public_workspace"),
])
@pytest.mark.parametrize(
    '_setup_role, access_rights',
    [
        pytest.param(None, lambda username: {"read": username, "write": username}, id="only_owner_permissions"),
        pytest.param("TEST_ROLE", lambda username: {"read": f"{username},TEST_ROLE", "write": username}, id="shared_with_role"),
    ],
    indirect=["_setup_role"]
)
@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('oauth2_provider_mock')
def test_delete_user(setup_users_and_role, publication_type, workspace, _setup_role, access_rights):
    username, actor_name, _ = setup_users_and_role
    publication = 'test_delete_user_publication'
    access_rights = access_rights(username)
    if callable(workspace):
        workspace = workspace(username)
    process_client.publish_workspace_publication(publication_type, workspace, publication, actor_name=username, access_rights=access_rights)

    # check if publications exists
    publications = process_client.get_publications(publication_type, workspace=workspace, actor_name=username)
    assert any(pub.get('name') == publication for pub in publications), f"Publication {publication} was not created"

    # check if publication info exists
    with app.app_context():
        publication_info = layman_util.get_publication_info(workspace, publication_type, publication)
    assert isinstance(publication_info, dict) and publication_info, "Publication info cannot be empty"

    # check if workspace exists
    assert workspace_exists(workspace), f"Workspace '{workspace}' was not found"
    # check if user exists
    assert user_exists(username), f"User '{username}' was not found"

    response = process_client.delete_user(username, actor_name=actor_name)
    assert response.status_code == 200, response.json()

    # check if publication was deleted
    publications_after_delete = process_client.get_publications(publication_type, actor_name=username)
    assert not any(pub.get('name') == publication for pub in publications_after_delete), f"Publication {publications_after_delete} was not deleted"
    # check if publication info was deleted
    with app.app_context():
        publication_info = layman_util.get_publication_info(username, publication_type, publication)
    assert isinstance(publication_info, dict) and not publication_info, "Publication info should be empty"

    # check if workspace was deleted
    if username == workspace:
        assert not workspace_exists(username), f"Workspace '{username}' was not deleted"
    # check if user was deleted
    assert not user_exists(username), f"User '{username}' was not deleted"


@pytest.mark.parametrize('setup_users_for_testing_errors', [
    pytest.param(('non_existing_user', 'test_delete_user_negative2', 404, 57), id="non_existing_user"),
    pytest.param(('test_delete_user_negative', 'test_delete_user_negative2', 403, 30), id="forbidden_deletion"),
    pytest.param(('', 'test_delete_user_negative2', 404, None), id="empty_username"),
    pytest.param((ANONYM_USER, 'test_delete_user_negative2', 404, 57), id="deletion_by_anonym"),
    pytest.param((NONAME_USER, 'test_delete_user_negative2', 404, 57), id="deletion_by_noname"),
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


@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.parametrize('workspace', [
    pytest.param(lambda username: f"{username}", id="user_workspace"),
    pytest.param("public_workspace", id="public_workspace"),
])
@pytest.mark.parametrize(
    '_setup_role, access_rights',
    [
        pytest.param(None, lambda username: {"read": username, "write": username}, id="only_owner_permissions"),
        pytest.param("TEST_ROLE", lambda username: {"read": f"{username},TEST_ROLE", "write": username}, id="shared_with_role"),
    ],
    indirect=["_setup_role"]
)
@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
def test_delete_self_with_publications(publication_type, workspace, _setup_role, access_rights):
    username = "test_delete_owner_only"
    publication = 'test_delete_user_publication_owner'
    access_rights = access_rights(username)
    if callable(workspace):
        workspace = workspace(username)
    process_client.reserve_username(username, actor_name=username)
    process_client.publish_workspace_publication(publication_type, workspace, publication, actor_name=username, access_rights=access_rights)
    process_client.delete_user(username, actor_name=username)
    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publication_type, publication)
    assert not publ_info, f"Publication {publication} in workspace {workspace} was not deleted"


@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
def test_delete_user_with_undeletable_publications(publication_type):
    # create publication with different users, roles write access rights
    rolename = 'TEST_ROLE'
    username = "test_delete_owner_writer"
    publication = 'test_delete_user_publication_writer'
    public_workspace = 'test_workspace'
    username2 = 'test_delete_writer'
    with app.app_context():
        role_service.ensure_role(rolename)
    access_rights = {
        'read': ','.join([username, username2, rolename]),
        'write': ','.join([username, username2, rolename])
    }
    users = process_client.get_users()
    if not any(user['username'] == username for user in users):
        process_client.reserve_username(username, actor_name=username)
    if not any(user['username'] == username2 for user in users):
        process_client.reserve_username(username2, actor_name=username2)
    process_client.publish_workspace_publication(publication_type, public_workspace, publication, actor_name=username, access_rights=access_rights)
    process_client.delete_user(username, actor_name=username)
    with app.app_context():
        publ_info = layman_util.get_publication_info(public_workspace, publication_type, publication)
    assert publ_info, f"Publication {publication} was deleted unexpectedly"
    access_rights = publ_info.get('access_rights', {})
    assert {tuple(sorted(v)) for v in access_rights.values()} == {tuple(sorted([username2, rolename]))}
    role_service.delete_role(rolename)


@pytest.mark.parametrize('setup_user_or_everyone', [
    pytest.param(('test_delete_owner_reader', 'test_delete_reader', 'test_delete_user_publication_reader'), id="reader_user"),
    pytest.param(('test_delete_owner_reader', RIGHTS_EVERYONE_ROLE, 'test_delete_user_publication_everyone'), id="reader_everyone"),
], indirect=True)
@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
def test_delete_shared_publications_with_readers(setup_user_or_everyone, publication_type):
    # create publication with different users read access rights
    username, reader, publication = setup_user_or_everyone
    public_workspace = 'test_workspace'
    access_rights = {
        'read': f"{username},{reader}",
        'write': f"{username}"
    }
    process_client.publish_workspace_publication(publication_type, public_workspace, publication, actor_name=username,
                                                 access_rights=access_rights)
    with pytest.raises(LaymanError) as exc_info:
        process_client.delete_user(username, actor_name=username)
    assert exc_info.value.code == 58, f"Unexpected error code: {exc_info.value.code}"
    response_data = exc_info.value.data
    expected_publications = [{
        "name": publication,
        "workspace": public_workspace,
        "type": publication_type,
    }]
    unable_delete_publications = [
        {
            "name": pub["name"],
            "workspace": pub["workspace"],
            "type": pub["type"],
        }
        for pub in response_data["unable_to_delete_publications"]
    ]
    assert unable_delete_publications == expected_publications, (
        f"expected publications are different {unable_delete_publications}"

    )
    process_client.delete_workspace_publications(publication_type, public_workspace, actor_name=username)


def workspace_exists(workspace):
    with app.app_context():
        return workspace in layman_util.get_workspaces()


def user_exists(username):
    users = process_client.get_users()
    return any(user.get("username") == username for user in users)


@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock', 'ensure_external_db')
def test_layer_with_external_table():
    username = 'test_delete_user_external_table_user'
    username_2 = 'test_delete_user_external_table_user_reader'
    workspace = 'test_delete_user_workspace'
    layername = 'test_delete_user_external_table_layer'
    process_client.reserve_username(username, actor_name=username)
    process_client.reserve_username(username_2, actor_name=username_2)

    external_db_table = 'small_layer'
    external_db_schema = 'public'

    external_db.import_table(input_file_path='sample/layman.layer/small_layer.geojson',
                             schema=external_db_schema,
                             table=external_db_table,
                             )

    process_client.publish_workspace_publication(process_client.LAYER_TYPE, workspace, layername,
                                                 external_table_uri=f"{external_db.URI_STR}?schema={external_db_schema}&table={external_db_table}",
                                                 actor_name=username,
                                                 access_rights={'read': f"{username}, {username_2}",
                                                                'write': f"{username}, {username_2}"
                                                                })

    process_client.delete_user(username, actor_name=username)
    process_client.delete_user(username_2, actor_name=username_2)
    # drop external table
    external_db.drop_table(schema=external_db_schema,
                           name=external_db_table)
