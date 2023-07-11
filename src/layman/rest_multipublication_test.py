import pytest

from layman import LaymanError
from test_tools import process_client


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
