import pytest

from test_tools import process_client, role_service as role_service_util


@pytest.mark.timeout(60)
class TestDeletePublicationsClass:
    owner = 'test_delete_publications_owner'
    deleter = 'test_delete_publications_deleter'
    ROLE = 'TEST_DELETE_PUBLICATIONS_ROLE'

    @pytest.fixture(scope="class")
    def provide_data(self, request):
        process_client.ensure_reserved_username(self.owner)
        process_client.ensure_reserved_username(self.deleter)
        role_service_util.ensure_user_role(self.deleter, self.ROLE)
        yield
        if request.node.session.testsfailed == 0 and not request.config.option.nocleanup:
            role_service_util.delete_user_role(self.deleter, self.ROLE)
            role_service_util.delete_role(self.ROLE)

    def check_delete(self,
                     actor_name,
                     after_delete_publications,
                     remaining_publications,
                     publ_type,
                     ):
        delete_json = process_client.delete_workspace_publications(publ_type, self.owner, actor_name=actor_name)
        publication_set = {publication['name'] for publication in delete_json}
        assert after_delete_publications == publication_set

        get_json = process_client.get_publications(publ_type, workspace=self.owner,
                                                   actor_name=self.owner)
        publication_set = {publication['name'] for publication in get_json}
        assert remaining_publications == publication_set

    @pytest.mark.parametrize('publ_type', process_client.PUBLICATION_TYPES)
    @pytest.mark.parametrize('available_write_rights', [
        pytest.param('EVERYONE', id='access_by_everyone'),
        pytest.param(f'{owner},{deleter}', id='access_by_user'),
        pytest.param(f'{owner},{ROLE}', id='access_by_role'),
    ])
    @pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman', 'provide_data')
    def test_delete_publications_by_user(self,
                                         publ_type,
                                         available_write_rights):
        owner = self.owner

        publication_a = 'test_delete_publications_publication_a'
        publication_b = 'test_delete_publications_publication_b'
        publications = [(publication_a, {'read': 'EVERYONE', 'write': owner}),
                        (publication_b, {'read': 'EVERYONE', 'write': available_write_rights}),
                        ]

        for (name, access_rights) in publications:
            process_client.publish_workspace_publication(publ_type, owner, name, access_rights=access_rights,
                                                         actor_name=owner)

        response = process_client.get_publications(publ_type, workspace=owner, actor_name=owner)
        assert len(response) == len(publications)

        # Delete by other user with rights only for one layer
        self.check_delete(self.deleter,
                          {publication_b, },
                          {publication_a, },
                          publ_type,
                          )

        # Delete by owner, everything is deleted
        self.check_delete(owner,
                          {publication_a, },
                          set(),
                          publ_type,
                          )
