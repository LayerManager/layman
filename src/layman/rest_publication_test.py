import pytest
import json

from test import process, process_client
from layman.common.micka import util as micka_util

ensure_layman = process.ensure_layman
liferay_mock = process.liferay_mock


@pytest.mark.parametrize("publish_method, patch_method, delete_method", [
    (process_client.publish_layer, process_client.patch_layer, process_client.delete_layer,),
    (process_client.publish_map, process_client.patch_map, process_client.delete_map,),
])
@pytest.mark.usefixtures('ensure_layman')
def test_wrong_post(publish_method,
                    patch_method,
                    delete_method):
    def check_response(resp):
        assert resp.status_code == 400, (resp.status_code, r.text)
        resp_json = json.loads(resp.text)
        assert resp_json['code'] == 43, (resp.status_code, resp.text)
        assert resp_json['message'] == 'Wrong access rights.', (resp.status_code, resp.text)

    workspace = 'test_wrong_post_workspace'
    publication = 'test_wrong_post_publication'

    r = publish_method(workspace, publication, access_rights={'read': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = publish_method(workspace, publication, access_rights={'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = publish_method(workspace, publication, access_rights={'read': 'EVRBODY', 'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    publish_method(workspace, publication)

    r = patch_method(workspace, publication, access_rights={'read': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = patch_method(workspace, publication, access_rights={'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = patch_method(workspace, publication, access_rights={'read': 'EVRBODY', 'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = patch_method(workspace, publication)

    delete_method(workspace, publication)


class TestSoapClass:
    username = 'test_rest_soap_user'
    publ_name_prefix = 'test_rest_soap_'
    authz_headers = process_client.get_authz_headers(username)
    access_rights_rowo = {'read': f"{username}", 'write': f"{username}"}
    access_rights_rewo = {'read': f"{username},EVERYONE", 'write': f"{username}"}
    access_rights_rewe = {'read': f"{username},EVERYONE", 'write': f"{username},EVERYONE"}

    @pytest.fixture(scope='class')
    def reserve_username(self):
        process_client.reserve_username(self.username, headers=self.authz_headers)
        yield

    @pytest.mark.usefixtures('liferay_mock', 'ensure_layman', 'reserve_username')
    @pytest.mark.parametrize('params_and_expected_list', [
        # (input access rights, expected public visibility of metadata record)
        [(access_rights_rowo, False), (access_rights_rewe, True)],
        [(access_rights_rewo, True)],
        [(access_rights_rewe, True), (access_rights_rowo, False)],
    ])
    @pytest.mark.parametrize('publ_type', process_client.PUBLICATION_TYPES)
    def test_soap_authz(self, publ_type, params_and_expected_list):
        username = self.username
        publ_name_prefix = self.publ_name_prefix
        authz_headers = self.authz_headers

        post_method = process_client.get_post_publications_method(publ_type)
        patch_method = process_client.get_patch_publication_method(publ_type)
        publ_name = f"{publ_name_prefix}{publ_type.split('.')[-1]}"
        get_method = process_client.get_get_publication_method(publ_type)
        delete_method = process_client.get_delete_publication_method(publ_type)

        for idx, (access_rights, anonymous_visibility) in enumerate(params_and_expected_list):
            write_method = patch_method if idx > 0 else post_method

            write_method(username,
                         publ_name,
                         headers=authz_headers,
                         access_rights=access_rights)

            publ_uuid = get_method(username, publ_name, headers=authz_headers)['uuid']
            publ_muuid = f"m-{publ_uuid}"
            assert micka_util.get_number_of_records(publ_muuid, use_authn=True) > 0
            anon_number_of_records = micka_util.get_number_of_records(publ_muuid, use_authn=False)
            assert bool(anon_number_of_records) == anonymous_visibility, \
                f"muuid={publ_muuid}, access_rights={access_rights}, number_of_records={anon_number_of_records}"

        delete_method(username,
                      publ_name,
                      headers=authz_headers)
