import pytest
from layman import settings, LaymanError
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

            get_json = process_client.get_workspace_publications(publ_type, workspace=owner,
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
    publications = [
        (workspace1, 'test_get_publications_publication1e', {
            'title': 'Public publication in public workspace'
        }),
        (workspace2, 'test_get_publications_publication2e', {
            'headers': authn_headers_user2,
            'title': '\'Too yellow horse\' means "Příliš žluťoučký kůň".',
            'access_rights': {'read': settings.RIGHTS_EVERYONE_ROLE,
                              'write': settings.RIGHTS_EVERYONE_ROLE},
        }),
        (workspace2, 'test_get_publications_publication2o', {
            'headers': authn_headers_user2,
            'title': 'Příliš jiný žluťoučký kůň úpěl ďábelské ódy',
            'access_rights': {'read': workspace2,
                              'write': workspace2},
        }),
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

    @pytest.mark.parametrize('headers, query_params, expected_publications', [
        (authn_headers_user2, {}, [(workspace1, 'test_get_publications_publication1e'),
                                   (workspace2, 'test_get_publications_publication2e'),
                                   (workspace2, 'test_get_publications_publication2o'),
                                   ],),
        (None, {}, [(workspace1, 'test_get_publications_publication1e'),
                    (workspace2, 'test_get_publications_publication2e'),
                    ],),
        (authn_headers_user2, {'full_text_filter': 'kůň'}, [(workspace2, 'test_get_publications_publication2e'),
                                                            (workspace2, 'test_get_publications_publication2o'),
                                                            ],),
        (None, {'full_text_filter': 'The Fačřš_tÚŮTŤsa   "  a34432[;] ;.\\Ra\'\'ts'}, list(),),
        (authn_headers_user2, {'full_text_filter': '\'Too yellow horse\' means "Příliš žluťoučký kůň".'}, [
            (workspace2, 'test_get_publications_publication2e'),
            (workspace2, 'test_get_publications_publication2o'),
        ],),
        (authn_headers_user2, {'full_text_filter': 'mean'}, [(workspace2, 'test_get_publications_publication2e'),
                                                             ],),
        (authn_headers_user2, {'full_text_filter': 'jiný další kůň'}, [(workspace2, 'test_get_publications_publication2o'),
                                                                       (workspace2, 'test_get_publications_publication2e'),
                                                                       ],),
        (authn_headers_user2, {'full_text_filter': 'workspace publication'}, [
            (workspace1, 'test_get_publications_publication1e'),
        ],),
        (authn_headers_user2, {'order_by': 'title'}, [(workspace2, 'test_get_publications_publication2o'),
                                                      (workspace1, 'test_get_publications_publication1e'),
                                                      (workspace2, 'test_get_publications_publication2e'),
                                                      ],),
        (authn_headers_user2, {'order_by': 'last_change'}, [(workspace2, 'test_get_publications_publication2o'),
                                                            (workspace2, 'test_get_publications_publication2e'),
                                                            (workspace1, 'test_get_publications_publication1e'),
                                                            ],),
    ])
    @pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
    @pytest.mark.usefixtures('liferay_mock', 'ensure_layman', 'provide_data')
    def test_get_publications(self, publication_type, headers, query_params, expected_publications):
        infos = process_client.get_publications(publication_type, headers, query_params=query_params)
        info_publications = [(info['workspace'], info['name']) for info in infos]
        assert set(expected_publications) == set(info_publications)
        assert expected_publications == info_publications


@pytest.mark.parametrize('query_params, error_code, error_specification,', [
    ({'order_by': 'gdasfda'}, (2, 400), {'parameter': 'order_by'}),
    ({'order_by': 'full_text'}, (48, 400), dict()),
])
@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman', )
def test_get_publications_errors(publication_type, query_params, error_code, error_specification):
    with pytest.raises(LaymanError) as exc_info:
        process_client.get_publications(publication_type, query_params=query_params)
    assert exc_info.value.code == error_code[0]
    assert exc_info.value.http_code == error_code[1]
    for key, value in error_specification.items():
        assert exc_info.value.data[key] == value, (exc_info, error_specification)
