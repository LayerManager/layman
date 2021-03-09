import pytest
from layman import settings
from test import process_client


class TestDeletePublicationsClass:
    owner = 'test_delete_publications_owner'
    deleter = 'test_delete_publications_deleter'
    authn_headers_owner = process_client.get_authz_headers(owner)
    authn_headers_deleter = process_client.get_authz_headers(deleter)

    @pytest.fixture(scope="class")
    def provide_data(self):
        process_client.ensure_reserved_username(self.owner, self.authn_headers_owner)
        process_client.ensure_reserved_username(self.deleter, self.authn_headers_deleter)
        yield

    @pytest.mark.parametrize('publ_type', process_client.PUBLICATION_TYPES)
    @pytest.mark.usefixtures('liferay_mock', 'ensure_layman', 'provide_data')
    def test_delete_publications(self,
                                 publ_type):
        def check_delete(headers,
                         after_delete_publications,
                         remaining_publications):
            delete_json = process_client.delete_workspace_publications(publ_type, owner, headers=headers)
            publication_set = {publication['name'] for publication in delete_json}
            assert after_delete_publications == publication_set

            get_json = process_client.get_workspace_publications(publ_type, workspace=owner, headers=authn_headers_owner)
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
            process_client.publish_workspace_publication(publ_type, owner, name, access_rights=access_rights, headers=authn_headers_owner)

        rv = process_client.get_workspace_publications(publ_type, workspace=owner, headers=authn_headers_owner)
        assert len(rv) == len(publications)

        # Delete by other user with rights only for one layer
        check_delete(authn_headers_deleter,
                     {publication_b, },
                     {publication_a, })

        # Delete by owner, everything is deleted
        check_delete(authn_headers_owner,
                     {publication_a, },
                     set())


class TestGetPublications:
    workspace1 = 'test_get_publications_workspace1'
    workspace2 = 'test_get_publications_workspace2'
    authn_headers_user2 = process_client.get_authz_headers(workspace2)
    publications = [(workspace1, 'test_get_publications_publication1e', dict()),
                    (workspace2, 'test_get_publications_publication2e', {'headers': authn_headers_user2,
                                                                         'access_rights': {'read': settings.RIGHTS_EVERYONE_ROLE,
                                                                                           'write': settings.RIGHTS_EVERYONE_ROLE}, }),
                    (workspace2, 'test_get_publications_publication2o', {'headers': authn_headers_user2,
                                                                         'access_rights': {'read': workspace2,
                                                                                           'write': workspace2}, }),
                    ]

    @pytest.fixture(scope="class")
    def provide_data(self):
        process_client.ensure_reserved_username(self.workspace2, self.authn_headers_user2)

        for publication_type in process_client.PUBLICATION_TYPES:
            for publication in self.publications:
                process_client.publish_workspace_publication(publication_type, publication[0], publication[1], **publication[2])
        yield
        for publication_type in process_client.PUBLICATION_TYPES:
            for publication in self.publications:
                process_client.delete_workspace_publication(publication_type, publication[0], publication[1],
                                                            publication[2].get('headers'))

    @pytest.mark.parametrize('headers, expected_publications', [
        (authn_headers_user2, [(workspace1, 'test_get_publications_publication1e'),
                               (workspace2, 'test_get_publications_publication2e'),
                               (workspace2, 'test_get_publications_publication2o'),
                               ], ),
        (None, [(workspace1, 'test_get_publications_publication1e'), (workspace2, 'test_get_publications_publication2e'), ],),
    ])
    @pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
    @pytest.mark.usefixtures('liferay_mock', 'ensure_layman', 'provide_data')
    def test_get_publications(self, publication_type, headers, expected_publications):
        infos = process_client.get_publications(publication_type, headers, )
        info_publications = [(info.get('workspace'), info.get('name')) for info in infos]
        assert expected_publications == info_publications
