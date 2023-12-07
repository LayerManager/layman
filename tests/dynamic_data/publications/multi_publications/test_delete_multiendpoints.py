import pytest

from test_tools import process_client


@pytest.mark.timeout(60)
class TestDeletePublicationsClass:
    owner = 'test_delete_publications_owner'
    deleter = 'test_delete_publications_deleter'

    @pytest.fixture(scope="class")
    def provide_data(self):
        process_client.ensure_reserved_username(self.owner)
        process_client.ensure_reserved_username(self.deleter)
        yield

    @pytest.mark.parametrize('publ_type', process_client.PUBLICATION_TYPES)
    @pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman', 'provide_data')
    def test_delete_publications(self,
                                 publ_type):
        def check_delete(headers,
                         after_delete_publications,
                         remaining_publications):
            delete_json = process_client.delete_workspace_publications(publ_type, owner, headers=headers)
            publication_set = {publication['name'] for publication in delete_json}
            assert after_delete_publications == publication_set

            get_json = process_client.get_publications(publ_type, workspace=owner,
                                                       headers=authn_headers_owner)
            publication_set = {publication['name'] for publication in get_json}
            assert remaining_publications == publication_set

        owner = self.owner
        authn_headers_owner = self.authn_headers_owner
        authn_headers_deleter = self.authn_headers_deleter

        publication_a = 'test_delete_publications_publication_a'
        publication_b = 'test_delete_publications_publication_b'
        publications = [(publication_a, {'read': 'EVERYONE', 'write': owner}),
                        (publication_b, {'read': 'EVERYONE', 'write': 'EVERYONE'}),
                        ]

        for (name, access_rights) in publications:
            process_client.publish_workspace_publication(publ_type, owner, name, access_rights=access_rights,
                                                         headers=authn_headers_owner)

        response = process_client.get_publications(publ_type, workspace=owner, headers=authn_headers_owner)
        assert len(response) == len(publications)

        # Delete by other user with rights only for one layer
        check_delete(authn_headers_deleter,
                     {publication_b, },
                     {publication_a, })

        # Delete by owner, everything is deleted
        check_delete(authn_headers_owner,
                     {publication_a, },
                     set())
