import pytest

import crs as crs_def
from layman import LaymanError, settings
from test_tools import process_client, prime_db_schema_client


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
    @pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman', 'provide_data')
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

        response = process_client.get_workspace_publications(publ_type, workspace=owner, headers=authn_headers_owner)
        assert len(response) == len(publications)

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

    publication_1e_2_4x6_6 = 'test_get_publications_publication1e_2_4x6_6'
    publication_1e_3_3x3_3 = 'test_get_publications_publication1e_3_3x3_3'
    publication_1e_3_7x5_9 = 'test_get_publications_publication1e_3_7x5_9'
    publication_2e_3_3x5_5 = 'test_get_publications_publication2e_3_3x5_5'
    publication_2o_2_2x4_4 = 'test_get_publications_publication2o_2_2x4_4'

    publications = [
        (workspace1, publication_1e_2_4x6_6, {
            'title': 'Příliš jiný žluťoučký kůň úpěl ďábelské ódy (publication)',
            'bbox': (2000, 4000, 6000, 6000),
            'crs': crs_def.EPSG_3857,
        }),
        (workspace1, publication_1e_3_3x3_3, {
            'title': 'Jednobodová publikace (publication)',
            'bbox': (3000, 3000, 3000, 3000),
            'crs': crs_def.EPSG_3857,
        }),
        (workspace1, publication_1e_3_7x5_9, {
            'title': 'Public publication in public workspace (publication)',
            'bbox': (3000, 7000, 5000, 9000),
            'crs': crs_def.EPSG_3857,
        }),
        (workspace2, publication_2e_3_3x5_5, {
            'title': '\'Too yellow horse\' means "Příliš žluťoučký kůň". (publication)',
            'bbox': (3000, 3000, 5000, 5000),
            'crs': crs_def.EPSG_3857,
            'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                              'write': {settings.RIGHTS_EVERYONE_ROLE}},
            'actor': workspace2,
        },
        ),
        (workspace2, publication_2o_2_2x4_4, {
            'title': 'Příliš jiný žluťoučký kůň úpěl ďábelské ódy (publication)',
            'actor': workspace2,
            'access_rights': {'read': {workspace2},
                              'write': {workspace2}},
            'bbox': (2000, 2000, 4000, 4000),
            'crs': crs_def.EPSG_3857,
        },
        ),
    ]

    @pytest.fixture(scope="class")
    def provide_data(self):
        process_client.ensure_reserved_username(self.workspace2, self.authn_headers_user2)
        prime_db_schema_client.ensure_workspace(self.workspace1)

        for publ_type in process_client.PUBLICATION_TYPES:
            geodata_type = 'vector' if publ_type == process_client.LAYER_TYPE else None
            for workspace, publ_name, publ_params in self.publications:
                prime_db_schema_client.post_workspace_publication(publ_type, workspace, publ_name, **publ_params,
                                                                  geodata_type=geodata_type)
        yield
        prime_db_schema_client.clear_workspaces([self.workspace1, self.workspace2])

    @staticmethod
    def assert_response(response, expected_publications, expected_headers):
        infos = response.json()
        info_publications = [(info['workspace'], info['name']) for info in infos]
        assert set(expected_publications) == set(info_publications)
        assert expected_publications == info_publications
        for header, value in expected_headers.items():
            assert header in response.headers, response.headers
            assert value == response.headers[header], response.headers

    @staticmethod
    @pytest.mark.parametrize('headers, query_params, expected_publications, expected_headers', [
        (authn_headers_user2, {}, [(workspace1, publication_1e_2_4x6_6),
                                   (workspace1, publication_1e_3_3x3_3),
                                   (workspace1, publication_1e_3_7x5_9),
                                   (workspace2, publication_2e_3_3x5_5),
                                   (workspace2, publication_2o_2_2x4_4),
                                   ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 1-5/5'
        },),
        (None, {}, [(workspace1, publication_1e_2_4x6_6),
                    (workspace1, publication_1e_3_3x3_3),
                    (workspace1, publication_1e_3_7x5_9),
                    (workspace2, publication_2e_3_3x5_5),
                    ], {
            'X-Total-Count': '4',
            'Content-Range': 'items 1-4/4'
        },),
        (authn_headers_user2, {'full_text_filter': 'kůň'}, [(workspace1, publication_1e_2_4x6_6),
                                                            (workspace2, publication_2e_3_3x5_5),
                                                            (workspace2, publication_2o_2_2x4_4),
                                                            ], {
            'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3'
        },),
        (None, {'full_text_filter': 'The Fačřš_tÚŮTŤsa   "  a34432[;] ;.\\Ra\'\'ts'}, [], {
            'X-Total-Count': '0',
            'Content-Range': 'items 0-0/0'
        },),
        (authn_headers_user2, {'full_text_filter': '\'Too yellow horse\' means "Příliš žluťoučký kůň".'}, [
            (workspace2, publication_2e_3_3x5_5),
            (workspace1, publication_1e_2_4x6_6),
            (workspace2, publication_2o_2_2x4_4),
        ], {
            'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3'
        },),
        (authn_headers_user2, {'full_text_filter': 'mean'}, [(workspace2, publication_2e_3_3x5_5),
                                                             ], {
            'X-Total-Count': '1',
            'Content-Range': 'items 1-1/1'
        },),
        (authn_headers_user2, {'full_text_filter': 'jiný další kůň'}, [(workspace1, publication_1e_2_4x6_6),
                                                                       (workspace2, publication_2o_2_2x4_4),
                                                                       (workspace2, publication_2e_3_3x5_5),
                                                                       ], {
            'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3'
        },),
        (authn_headers_user2, {'full_text_filter': 'jiný další kůň', 'order_by': 'full_text'}, [
            (workspace1, publication_1e_2_4x6_6),
            (workspace2, publication_2o_2_2x4_4),
            (workspace2, publication_2e_3_3x5_5),
        ], {
            'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3'
        },),
        (authn_headers_user2, {'full_text_filter': 'workspace publication'}, [
            (workspace1, publication_1e_3_7x5_9),
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            (workspace2, publication_2e_3_3x5_5),
            (workspace2, publication_2o_2_2x4_4),
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 1-5/5'
        },),
        (authn_headers_user2, {'full_text_filter': 'TOUCK'}, [
            (workspace1, publication_1e_2_4x6_6),
            (workspace2, publication_2e_3_3x5_5),
            (workspace2, publication_2o_2_2x4_4),
        ], {
            'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3'
        },),
        (authn_headers_user2, {'order_by': 'title'}, [(workspace1, publication_1e_3_3x3_3),
                                                      (workspace1, publication_1e_2_4x6_6),
                                                      (workspace2, publication_2o_2_2x4_4),
                                                      (workspace1, publication_1e_3_7x5_9),
                                                      (workspace2, publication_2e_3_3x5_5),
                                                      ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 1-5/5'
        },),
        (authn_headers_user2, {'order_by': 'last_change'}, [(workspace2, publication_2o_2_2x4_4),
                                                            (workspace2, publication_2e_3_3x5_5),
                                                            (workspace1, publication_1e_3_7x5_9),
                                                            (workspace1, publication_1e_3_3x3_3),
                                                            (workspace1, publication_1e_2_4x6_6),
                                                            ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 1-5/5'
        },),
        (authn_headers_user2, {'order_by_list': ['bbox'],
                               'ordering_bbox': ','.join(str(c) for c in (2999, 2999, 5001, 5001))}, [
            (workspace2, publication_2e_3_3x5_5),
            (workspace1, publication_1e_2_4x6_6),
            (workspace2, publication_2o_2_2x4_4),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 1-5/5'
        },),
        (authn_headers_user2, {'order_by_list': ['bbox'],
                               'ordering_bbox': ','.join(str(c) for c in (0.0269405, 0.0269405, 0.0449247, 0.0449247)),  # EPSG:3857 (2999, 2999, 5001, 5001)
                               'ordering_bbox_crs': 'EPSG:4326',
                               }, [
            (workspace2, publication_2e_3_3x5_5),
            (workspace1, publication_1e_2_4x6_6),
            (workspace2, publication_2o_2_2x4_4),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 1-5/5'
        },),
        (authn_headers_user2, {'order_by_list': ['bbox'],
                               'ordering_bbox': ','.join(str(c) for c in (3001, 3001, 3001, 3001))}, [
            (workspace2, publication_2e_3_3x5_5),
            (workspace2, publication_2o_2_2x4_4),
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 1-5/5'
        },),
        (authn_headers_user2, {'order_by_list': ['bbox'],
                               'ordering_bbox': ','.join(str(c) for c in (3001, 3001, 3001, 3001)),
                               'ordering_bbox_crs': 'EPSG:3857', }, [
            (workspace2, publication_2e_3_3x5_5),
            (workspace2, publication_2o_2_2x4_4),
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 1-5/5'
        },),
        (authn_headers_user2, {'bbox_filter': ','.join(str(c) for c in (3001, 3001, 4999, 4999))}, [
            (workspace2, publication_2e_3_3x5_5),
            (workspace1, publication_1e_2_4x6_6),
            (workspace2, publication_2o_2_2x4_4),
        ], {
            'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3'
        },),
        (authn_headers_user2, {'bbox_filter': ','.join(str(c) for c in (4001, 4001, 4001, 4001))}, [
            (workspace2, publication_2e_3_3x5_5),
            (workspace1, publication_1e_2_4x6_6),
        ], {
            'X-Total-Count': '2',
            'Content-Range': 'items 1-2/2'
        },),
        (authn_headers_user2, {'limit': 2}, [
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            # (workspace1, publication_1e_3_7x5_9),
            # (workspace2, publication_2e_3_3x5_5),
            # (workspace2, publication_2o_2_2x4_4),
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 1-2/5'
        },),
        (authn_headers_user2, {'offset': 1}, [
            # (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
            (workspace2, publication_2e_3_3x5_5),
            (workspace2, publication_2o_2_2x4_4),
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 2-5/5'
        },),
        (authn_headers_user2, {'limit': 1, 'offset': 1}, [
            # (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            # (workspace1, publication_1e_3_7x5_9),
            # (workspace2, publication_2e_3_3x5_5),
            # (workspace2, publication_2o_2_2x4_4),
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 2-2/5'
        },),
        (authn_headers_user2, {'limit': 0, 'offset': 0}, [
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 0-0/5'
        },),
        (authn_headers_user2, {'limit': 6, 'offset': 3}, [
            # (workspace1, publication_1e_2_4x6_6),
            # (workspace1, publication_1e_3_3x3_3),
            # (workspace1, publication_1e_3_7x5_9),
            (workspace2, publication_2e_3_3x5_5),
            (workspace2, publication_2o_2_2x4_4),
        ], {
            'X-Total-Count': '5',
            'Content-Range': 'items 4-5/5'
        },),
        (
            authn_headers_user2, {'order_by': 'title',
                                  'full_text_filter': 'ódy',
                                  'bbox_filter': ','.join(str(c) for c in (3001, 3001, 4999, 4999)),
                                  'limit': 1,
                                  }, [
                (workspace1, publication_1e_2_4x6_6),
                # (workspace2, publication_2o_2_2x4_4), limit
            ], {'X-Total-Count': '2',
                'Content-Range': 'items 1-1/2'},),
        (
            authn_headers_user2, {'order_by': 'title',
                                  'full_text_filter': 'ódy',
                                  'bbox_filter': ','.join(str(c) for c in (3001, 3001, 4999, 4999)),
                                  'offset': 1,
                                  }, [
                # (workspace1, publication_1e_2_4x6_6), offset
                (workspace2, publication_2o_2_2x4_4),
            ], {'X-Total-Count': '2',
                'Content-Range': 'items 2-2/2'},),
        (
            authn_headers_user2, {'order_by': 'bbox',
                                  'full_text_filter': 'prilis',
                                  'bbox_filter': ','.join(str(c) for c in (2000, 2000, 6000, 6000)),
                                  'offset': 1,
                                  'limit': 1,
                                  }, [
                # (workspace1, publication_1e_2_4x6_6),
                (workspace2, publication_2e_3_3x5_5),
                # (workspace2, publication_2o_2_2x4_4),
            ], {'X-Total-Count': '3',
                'Content-Range': 'items 2-2/3'},),
        (
            authn_headers_user2, {'full_text_filter': 'prilis yellow',
                                  'bbox_filter': ','.join(str(c) for c in (2000, 2000, 6000, 6000)),
                                  'bbox_filter_crs': crs_def.EPSG_3857,
                                  'offset': 1,
                                  'limit': 1,
                                  }, [
                # (workspace2, publication_2e_3_3x5_5),
                (workspace1, publication_1e_2_4x6_6),
                # (workspace2, publication_2o_2_2x4_4),
            ], {'X-Total-Count': '3',
                'Content-Range': 'items 2-2/3'},),
        (
            authn_headers_user2, {'order_by': 'title',
                                  'full_text_filter': 'prilis',
                                  'bbox_filter': ','.join(str(c) for c in (2000, 2000, 6000, 6000)),
                                  'offset': 1,
                                  'limit': 1,
                                  }, [
                # (workspace1, publication_1e_2_4x6_6),
                (workspace2, publication_2o_2_2x4_4),
                # (workspace2, publication_2e_3_3x5_5),
            ], {'X-Total-Count': '3',
                'Content-Range': 'items 2-2/3'},),
        (
            authn_headers_user2, {'order_by': 'title',
                                  'full_text_filter': 'prilis',
                                  'bbox_filter': ','.join(str(c) for c in (0.0179663, 0.0179663, 0.0538989, 0.0538989)),  # EPSG:3857 (2000, 2000, 6000, 6000)
                                  'bbox_filter_crs': crs_def.EPSG_4326,
                                  'offset': 1,
                                  'limit': 1,
                                  }, [
                # (workspace1, publication_1e_2_4x6_6),
                (workspace2, publication_2o_2_2x4_4),
                # (workspace2, publication_2e_3_3x5_5),
            ], {'X-Total-Count': '3',
                'Content-Range': 'items 2-2/3'},),
        (
            authn_headers_user2, {'order_by': 'bbox',
                                  'bbox_filter': ','.join(str(c) for c in (0.0179663, 0.0179663, 0.0538989, 0.0538989)),  # EPSG:3857 (2000, 2000, 6000, 6000)
                                  'bbox_filter_crs': crs_def.EPSG_4326,
                                  'ordering_bbox': ','.join(str(c) for c in (2999, 2999, 5001, 5001)),
                                  'ordering_bbox_crs': crs_def.EPSG_3857,
                                  }, [
                (workspace2, publication_2e_3_3x5_5),
                (workspace1, publication_1e_2_4x6_6),
                (workspace2, publication_2o_2_2x4_4),
                (workspace1, publication_1e_3_3x3_3),
            ], {'X-Total-Count': '4',
                'Content-Range': 'items 1-4/4'},),
        (
            authn_headers_user2, {'order_by': 'bbox',
                                  'bbox_filter': ','.join(str(c) for c in (0.0179663, 0.0179663, 0.0538989, 0.0538989)),  # EPSG:3857 (2000, 2000, 6000, 6000)
                                  'bbox_filter_crs': crs_def.EPSG_4326,
                                  'ordering_bbox': ','.join(str(c) for c in (0.0269405, 0.0269405, 0.0449247, 0.0449247)),  # EPSG:3857 (2999, 2999, 5001, 5001)
                                  }, [
                (workspace2, publication_2e_3_3x5_5),
                (workspace1, publication_1e_2_4x6_6),
                (workspace2, publication_2o_2_2x4_4),
                (workspace1, publication_1e_3_3x3_3),
            ], {'X-Total-Count': '4',
                'Content-Range': 'items 1-4/4'},),
        (
            authn_headers_user2, {'order_by': 'last_change',
                                  'full_text_filter': 'prilis',
                                  'bbox_filter': ','.join(str(c) for c in (2000, 2000, 6000, 6000)),
                                  'offset': 1,
                                  'limit': 1,
                                  }, [
                # (workspace2, publication_2o_2_2x4_4),
                (workspace2, publication_2e_3_3x5_5),
                # (workspace1, publication_1e_2_4x6_6),
            ], {'X-Total-Count': '3',
                'Content-Range': 'items 2-2/3'},),
    ])
    @pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
    @pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman', 'provide_data')
    def test_get_publications(publication_type, headers, query_params, expected_publications, expected_headers, ):
        response = process_client.get_publications_response(publication_type, headers=headers, query_params=query_params)
        TestGetPublications.assert_response(response, expected_publications, expected_headers)

    @staticmethod
    @pytest.mark.parametrize('workspace, headers, query_params, expected_publications, expected_headers', [
        (workspace1, authn_headers_user2, {}, [
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3',
            },
        ),
        (workspace1, None, {}, [
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3',
            },
        ),
        (workspace1, None, {'full_text_filter': 'kůň'}, [
            (workspace1, publication_1e_2_4x6_6),
        ], {'X-Total-Count': '1',
            'Content-Range': 'items 1-1/1',
            },
        ),
        (workspace1, None, {'full_text_filter': 'The Fačřš_tÚŮTŤsa   "  a34432[;] ;.\\Ra\'\'ts'}, [], {
            'X-Total-Count': '0',
            'Content-Range': 'items 0-0/0',
        },),
        (workspace1, None, {'full_text_filter': '\'Too yellow horse\' means "Příliš žluťoučký kůň".'}, [
            (workspace1, publication_1e_2_4x6_6),
        ], {'X-Total-Count': '1',
            'Content-Range': 'items 1-1/1',
            },
        ),
        (workspace1, None, {'full_text_filter': 'mean'}, [], {
            'X-Total-Count': '0',
            'Content-Range': 'items 0-0/0',
        },),
        (workspace1, None, {'full_text_filter': 'jiný další kůň'}, [
            (workspace1, publication_1e_2_4x6_6),
        ], {'X-Total-Count': '1',
            'Content-Range': 'items 1-1/1',
            },
        ),
        (workspace1, None, {'full_text_filter': 'jiný další kůň', 'order_by': 'full_text'}, [
            (workspace1, publication_1e_2_4x6_6),
        ], {'X-Total-Count': '1',
            'Content-Range': 'items 1-1/1',
            },
        ),
        (workspace1, None, {'full_text_filter': 'workspace publication'}, [
            (workspace1, publication_1e_3_7x5_9),
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3',
            },
        ),
        (workspace1, None, {'order_by': 'title'}, [
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3',
            },
        ),
        (workspace1, None, {'order_by': 'last_change'}, [
            (workspace1, publication_1e_3_7x5_9),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_2_4x6_6),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3',
            },
        ),
        (workspace1, None, {'order_by_list': ['bbox'],
                            'ordering_bbox': ','.join(str(c) for c in (0.0269405, 0.0269405, 0.0449247, 0.0449247)),  # EPSG:3857 (2999, 2999, 5001, 5001)
                            'ordering_bbox_crs': 'EPSG:4326'}, [
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3',
            },
        ),
        (workspace1, None, {'order_by_list': ['bbox'],
                            'ordering_bbox': ','.join(str(c) for c in (3001, 3001, 3001, 3001)),
                            'ordering_bbox_crs': 'EPSG:3857'}, [
            (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 1-3/3',
            },
        ),
        (workspace1, None, {'bbox_filter': ','.join(str(c) for c in (3001, 3001, 4999, 4999))}, [
            (workspace1, publication_1e_2_4x6_6),
        ], {'X-Total-Count': '1',
            'Content-Range': 'items 1-1/1',
            },
        ),
        (workspace1, None, {'bbox_filter': ','.join(str(c) for c in (4001, 4001, 4001, 4001))}, [
            (workspace1, publication_1e_2_4x6_6),
        ], {'X-Total-Count': '1',
            'Content-Range': 'items 1-1/1',
            },
        ),
        (workspace1, None, {'limit': 1}, [
            (workspace1, publication_1e_2_4x6_6),
            # (workspace1, publication_1e_3_3x3_3),
            # (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 1-1/3',
            },
        ),
        (workspace1, None, {'offset': 1}, [
            # (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 2-3/3',
            },
        ),
        (workspace1, None, {'limit': 1, 'offset': 1}, [
            # (workspace1, publication_1e_2_4x6_6),
            (workspace1, publication_1e_3_3x3_3),
            # (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 2-2/3',
            },
        ),
        (workspace1, None, {'limit': 0, 'offset': 0}, [
            # (workspace1, publication_1e_2_4x6_6),
            # (workspace1, publication_1e_3_3x3_3),
            # (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 0-0/3',
            },
        ),
        (workspace1, None, {'limit': 6, 'offset': 2}, [
            # (workspace1, publication_1e_2_4x6_6),
            # (workspace1, publication_1e_3_3x3_3),
            (workspace1, publication_1e_3_7x5_9),
        ], {'X-Total-Count': '3',
            'Content-Range': 'items 3-3/3',
            },
        ),
        (workspace1, None, {'order_by': 'title',
                            'full_text_filter': 'ódy',
                            'bbox_filter': ','.join(str(c) for c in (3001, 3001, 4999, 4999)),
                            'limit': 1,
                            }, [
            (workspace1, publication_1e_2_4x6_6),
        ], {'X-Total-Count': '1',
            'Content-Range': 'items 1-1/1',
            },
        ),
        (workspace1, None, {'order_by': 'title',
                            'full_text_filter': 'ódy',
                            'bbox_filter': ','.join(str(c) for c in (3001, 3001, 4999, 4999)),
                            'offset': 1,
                            }, [
            # (workspace1, publication_1e_2_4x6_6), offset
        ], {'X-Total-Count': '1',
            'Content-Range': 'items 0-0/1',
            },
        ),
        (workspace2, authn_headers_user2, {'order_by': 'bbox',
                                           'full_text_filter': 'prilis',
                                           'bbox_filter': ','.join(str(c) for c in (2000, 2000, 6000, 6000)),
                                           'offset': 1,
                                           'limit': 1,
                                           }, [
            # (workspace2, publication_2e_3_3x5_5),
            (workspace2, publication_2o_2_2x4_4),
        ], {'X-Total-Count': '2',
            'Content-Range': 'items 2-2/2',
            },
        ),
        (workspace2, authn_headers_user2, {'full_text_filter': 'prilis yellow',
                                           'bbox_filter': ','.join(str(c) for c in (2000, 2000, 6000, 6000)),
                                           'offset': 1,
                                           'limit': 1,
                                           }, [
            # (workspace2, publication_2e_3_3x5_5),
            (workspace2, publication_2o_2_2x4_4),
        ], {'X-Total-Count': '2',
            'Content-Range': 'items 2-2/2',
            },
        ),
        (workspace2, authn_headers_user2, {'order_by': 'title',
                                           'full_text_filter': 'prilis',
                                           'bbox_filter': ','.join(str(c) for c in (2000, 2000, 6000, 6000)),
                                           'bbox_filter_crs': crs_def.EPSG_3857,
                                           'offset': 1,
                                           'limit': 1,
                                           }, [
            # (workspace2, publication_2o_2_2x4_4),
            (workspace2, publication_2e_3_3x5_5),
        ], {'X-Total-Count': '2',
            'Content-Range': 'items 2-2/2',
            },
        ),
        (workspace2, authn_headers_user2, {'order_by': 'title',
                                           'full_text_filter': 'prilis',
                                           'bbox_filter': ','.join(str(c) for c in (0.0179663, 0.0179663, 0.0538989, 0.0538989)),
                                           # EPSG:3857 (2000, 2000, 6000, 6000)
                                           'bbox_filter_crs': crs_def.EPSG_4326,
                                           'offset': 1,
                                           'limit': 1,
                                           }, [
            # (workspace2, publication_2o_2_2x4_4),
            (workspace2, publication_2e_3_3x5_5),
        ], {'X-Total-Count': '2',
            'Content-Range': 'items 2-2/2',
            },
        ),
        (workspace2, authn_headers_user2, {'order_by': 'last_change',
                                           'full_text_filter': 'prilis',
                                           'bbox_filter': ','.join(str(c) for c in (2000, 2000, 6000, 6000)),
                                           'offset': 1,
                                           'limit': 1,
                                           }, [
            # (workspace2, publication_2o_2_2x4_4),
            (workspace2, publication_2e_3_3x5_5),
        ], {'X-Total-Count': '2',
            'Content-Range': 'items 2-2/2',
            },
        ),
    ])
    @pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
    @pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman', 'provide_data')
    def test_get_workspace_publications(publication_type, workspace, headers, query_params, expected_publications, expected_headers, ):
        response = process_client.get_workspace_publications_response(publication_type, workspace, headers=headers, query_params=query_params)
        TestGetPublications.assert_response(response, expected_publications, expected_headers)


@pytest.mark.parametrize('query_params, error_code, error_specification,', [
    ({'order_by': 'gdasfda'}, (2, 400), {'parameter': 'order_by'}),
    ({'order_by': 'full_text'}, (48, 400), {}),
    ({'order_by': 'bbox'}, (48, 400), {}),
    ({'order_by': 'title', 'ordering_bbox': '1,2,3,4'}, (48, 400), {}),
    ({'bbox_filter': '1,2,3,4,5'}, (2, 400), {'parameter': 'bbox_filter'}),
    ({'bbox_filter': '1,2,c,4'}, (2, 400), {'parameter': 'bbox_filter'}),
    ({'bbox_filter': '1,4,2,3'}, (2, 400), {'parameter': 'bbox_filter'}),
    ({'bbox_filter_crs': '3'}, (2, 400), {'parameter': 'bbox_filter_crs'}),
    ({'bbox_filter_crs': 'EPSG:3030'}, (2, 400), {'parameter': 'bbox_filter_crs'}),
    ({'bbox_filter_crs': 'CRS:84'}, (2, 400), {'parameter': 'bbox_filter_crs'}),
    ({'bbox_filter_crs': 'EPSG:3857'}, (48, 400), {}),
    ({'ordering_bbox': '1,2,3,4,5'}, (2, 400), {'parameter': 'ordering_bbox'}),
    ({'ordering_bbox': '1,2,c,4'}, (2, 400), {'parameter': 'ordering_bbox'}),
    ({'ordering_bbox': '1,4,2,3'}, (2, 400), {'parameter': 'ordering_bbox'}),
    ({'ordering_bbox_crs': 'EPSG:3857'}, (48, 400), {}),
    ({'limit': 'dasda'}, (2, 400), {'parameter': 'limit'}),
    ({'limit': '-7'}, (2, 400), {'parameter': 'limit'}),
    ({'offset': 'dasda'}, (2, 400), {'parameter': 'offset'}),
    ({'offset': '-7'}, (2, 400), {'parameter': 'offset'}),
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
