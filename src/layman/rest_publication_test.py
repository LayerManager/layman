import pytest
import datetime
from dateutil.parser import parse

from test import process_client
from layman import LaymanError, settings, app
from layman.common.prime_db_schema import util as db_util
from layman.common.micka import util as micka_util

db_schema = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.parametrize('publ_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman')
def test_wrong_post(publ_type):
    def check_response(exception):
        assert exception.value.http_code == 400
        assert exception.value.code == 43
        assert exception.value.message == 'Wrong access rights.'

    workspace = 'test_wrong_post_workspace'
    publication = 'test_wrong_post_publication'

    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_publication(publ_type, workspace, publication, access_rights={'read': 'EVRBODY'}, )
    check_response(exc_info)

    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_publication(publ_type, workspace, publication, access_rights={'write': 'EVRBODY'}, )
    check_response(exc_info)

    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_publication(publ_type, workspace, publication, access_rights={'read': 'EVRBODY', 'write': 'EVRBODY'}, )
    check_response(exc_info)

    process_client.publish_workspace_publication(publ_type, workspace, publication)

    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_publication(publ_type, workspace, publication, access_rights={'read': 'EVRBODY'}, )
    check_response(exc_info)

    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_publication(publ_type, workspace, publication, access_rights={'write': 'EVRBODY'}, )
    check_response(exc_info)

    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_publication(publ_type, workspace, publication, access_rights={'read': 'EVRBODY', 'write': 'EVRBODY'}, )
    check_response(exc_info)

    process_client.patch_workspace_publication(publ_type, workspace, publication)

    process_client.delete_workspace_publication(publ_type, workspace, publication)


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
        process_client.delete_workspace_publication(self.publication_type,
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

        post_method = process_client.publish_workspace_publication
        patch_method = process_client.patch_workspace_publication
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

            publ_uuid = process_client.get_workspace_publication(publ_type, username, publ_name, headers=authz_headers)['uuid']
            publ_muuid = f"m-{publ_uuid}"
            assert micka_util.get_number_of_records(publ_muuid, use_authn=True) > 0
            anon_number_of_records = micka_util.get_number_of_records(publ_muuid, use_authn=False)
            assert bool(anon_number_of_records) == anonymous_visibility, \
                f"muuid={publ_muuid}, access_rights={access_rights}, number_of_records={anon_number_of_records}"


@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman')
def test_updated_at(publication_type):
    workspace = 'test_update_at_workspace'
    publication = 'test_update_at_publication'

    query = f'''
    select p.updated_at
    from {db_schema}.publications p inner join
         {db_schema}.workspaces w on p.id_workspace = w.id
    where w.name = %s
      and p.type = %s
      and p.name = %s
    ;'''

    timestamp1 = datetime.datetime.now(datetime.timezone.utc)
    process_client.publish_workspace_publication(publication_type, workspace, publication)
    timestamp2 = datetime.datetime.now(datetime.timezone.utc)

    with app.app_context():
        results = db_util.run_query(query, (workspace, publication_type, publication))
    assert len(results) == 1 and len(results[0]) == 1, results
    updated_at_db = results[0][0]
    assert timestamp1 < updated_at_db < timestamp2

    info = process_client.get_workspace_publication(publication_type, workspace, publication)
    updated_at_rest_str = info['updated_at']
    updated_at_rest = parse(updated_at_rest_str)
    assert timestamp1 < updated_at_rest < timestamp2

    timestamp3 = datetime.datetime.now(datetime.timezone.utc)
    process_client.patch_workspace_publication(publication_type, workspace, publication, title='Title')
    timestamp4 = datetime.datetime.now(datetime.timezone.utc)

    with app.app_context():
        results = db_util.run_query(query, (workspace, publication_type, publication))
    assert len(results) == 1 and len(results[0]) == 1, results
    updated_at_db = results[0][0]
    assert timestamp3 < updated_at_db < timestamp4

    info = process_client.get_workspace_publication(publication_type, workspace, publication)
    updated_at_rest_str = info['updated_at']
    updated_at_rest = parse(updated_at_rest_str)
    assert timestamp3 < updated_at_rest < timestamp4

    process_client.delete_workspace_publication(publication_type, workspace, publication)
