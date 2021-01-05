import pytest
import json

from test import process, process_client
from layman.common.micka import util as micka_util

ensure_layman = process.ensure_layman
liferay_mock = process.liferay_mock


@pytest.mark.parametrize('publ_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman')
def test_wrong_post(publ_type):
    def check_response(resp):
        assert resp.status_code == 400, (resp.status_code, r.text)
        resp_json = json.loads(resp.text)
        assert resp_json['code'] == 43, (resp.status_code, resp.text)
        assert resp_json['message'] == 'Wrong access rights.', (resp.status_code, resp.text)

    workspace = 'test_wrong_post_workspace'
    publication = 'test_wrong_post_publication'

    r = process_client.publish_publication(publ_type, workspace, publication, access_rights={'read': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = process_client.publish_publication(publ_type, workspace, publication, access_rights={'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = process_client.publish_publication(publ_type, workspace, publication, access_rights={'read': 'EVRBODY', 'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    process_client.publish_publication(publ_type, workspace, publication)

    r = process_client.patch_publication(publ_type, workspace, publication, access_rights={'read': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = process_client.patch_publication(publ_type, workspace, publication, access_rights={'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = process_client.patch_publication(publ_type, workspace, publication, access_rights={'read': 'EVRBODY', 'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = process_client.patch_publication(publ_type, workspace, publication)

    process_client.delete_publication(publ_type, workspace, publication)


class TestSoapClass:
    username = 'test_rest_soap_user'
    publ_name_prefix = 'test_rest_soap_'
    authz_headers = process_client.get_authz_headers(username)
    access_rights_rowo = {'read': f"{username}", 'write': f"{username}"}
    access_rights_rewo = {'read': f"{username},EVERYONE", 'write': f"{username}"}
    access_rights_rewe = {'read': f"{username},EVERYONE", 'write': f"{username},EVERYONE"}
    publication_type = None
    publication_name = None

    @pytest.fixture(scope='class')
    def reserve_username(self):
        process_client.ensure_reserved_username(self.username, headers=self.authz_headers)
        yield

    @pytest.fixture()
    def clear_data(self):
        yield
        process_client.delete_publication(self.publication_type,
                                          self.username,
                                          self.publication_name,
                                          headers=self.authz_headers)

    @pytest.mark.flaky(reruns=5, reruns_delay=2)
    @pytest.mark.usefixtures('liferay_mock', 'ensure_layman', 'reserve_username', 'clear_data')
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

        post_method = process_client.publish_publication
        patch_method = process_client.patch_publication
        publ_name = f"{publ_name_prefix}{publ_type.split('.')[-1]}"
        self.publication_type = publ_type
        self.publication_name = publ_name

        for idx, (access_rights, anonymous_visibility) in enumerate(params_and_expected_list):
            write_method = patch_method if idx > 0 else post_method

            write_method(publ_type,
                         username,
                         publ_name,
                         headers=authz_headers,
                         access_rights=access_rights)

            publ_uuid = process_client.get_publication(publ_type, username, publ_name, headers=authz_headers)['uuid']
            publ_muuid = f"m-{publ_uuid}"
            assert micka_util.get_number_of_records(publ_muuid, use_authn=True) > 0
            anon_number_of_records = micka_util.get_number_of_records(publ_muuid, use_authn=False)
            assert bool(anon_number_of_records) == anonymous_visibility, \
                f"muuid={publ_muuid}, access_rights={access_rights}, number_of_records={anon_number_of_records}"
