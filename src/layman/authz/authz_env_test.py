import pytest
from layman.http import LaymanError
from test_tools import process, process_client


class TestPublicWorkspaceClass:
    publication_name = 'test_public_workspace_variable_publication'
    username = 'test_public_workspace_variable_user'
    workspace_name = 'test_public_workspace_variable_workspace'
    user_authz_headers = process_client.get_authz_headers(username)

    @pytest.fixture(scope="class")
    def setup_test_public_workspace_variable(self):
        username = self.username
        user_authz_headers = self.user_authz_headers
        env_vars = dict(process.AUTHN_SETTINGS)

        process.ensure_layman_function(env_vars)
        process_client.reserve_username(username, headers=user_authz_headers)
        yield

    @staticmethod
    @pytest.mark.usefixtures('oauth2_provider_mock', 'setup_test_public_workspace_variable')
    @pytest.mark.parametrize("publish_method, delete_method, workspace_suffix", [
        (process_client.publish_workspace_layer, process_client.delete_workspace_layer, '_layer',),
        (process_client.publish_workspace_map, process_client.delete_workspace_map, '_map',),
    ])
    @pytest.mark.parametrize(
        "create_public_workspace, publish_in_public_workspace, workspace_prefix, publication_name, authz_headers,"
        "user_can_create, anonymous_can_publish, anonymous_can_create,",
        [
            ('EVERYONE', 'EVERYONE', workspace_name + 'ee', publication_name, user_authz_headers, True, True, True,),
            (username, username, workspace_name + 'uu', publication_name, user_authz_headers, True, False, False,),
            ('', '', workspace_name + 'nn', publication_name, user_authz_headers, False, False, False,),
            (username, 'EVERYONE', workspace_name + 'ue', publication_name, user_authz_headers, True, True, False,),
        ],
    )
    def test_public_workspace_variable(create_public_workspace,
                                       publish_in_public_workspace,
                                       workspace_prefix,
                                       publication_name,
                                       authz_headers,
                                       user_can_create,
                                       anonymous_can_publish,
                                       anonymous_can_create,
                                       publish_method,
                                       delete_method,
                                       workspace_suffix,
                                       ):
        def can_not_publish(workspace_name,
                            publication_name,
                            publish_method,
                            authz_headers=None,
                            ):
            with pytest.raises(LaymanError) as exc_info:
                publish_method(workspace_name,
                               publication_name,
                               headers=authz_headers,
                               )
            assert exc_info.value.http_code == 403
            assert exc_info.value.code == 30
            assert exc_info.value.message == 'Unauthorized access'

        workspace_name = workspace_prefix + workspace_suffix
        workspace_name2 = workspace_name + '2'
        layername2 = publication_name + '2'
        env_vars = dict(process.AUTHN_SETTINGS)
        env_vars['GRANT_CREATE_PUBLIC_WORKSPACE'] = create_public_workspace
        env_vars['GRANT_PUBLISH_IN_PUBLIC_WORKSPACE'] = publish_in_public_workspace
        process.ensure_layman_function(env_vars)

        if user_can_create:
            publish_method(workspace_name, publication_name, headers=authz_headers)
            if anonymous_can_publish:
                publish_method(workspace_name, layername2)
                delete_method(workspace_name, layername2)
            delete_method(workspace_name, publication_name, headers=authz_headers)
        else:
            can_not_publish(workspace_name, publication_name, publish_method, authz_headers)

        if anonymous_can_create:
            publish_method(workspace_name2, publication_name)
            delete_method(workspace_name2, publication_name)
        else:
            can_not_publish(workspace_name2, publication_name, publish_method)
