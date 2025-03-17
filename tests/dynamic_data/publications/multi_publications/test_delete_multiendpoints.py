import os
import pytest

from test_tools import process_client, role_service as role_service_util
from tests import EnumTestTypes, EnumTestKeys


@pytest.mark.timeout(60)
class TestDeletePublicationsClass:
    owner = 'test_delete_publications_owner'
    deleter = 'test_delete_publications_deleter'
    ROLE = 'TEST_DELETE_PUBLICATIONS_ROLE'

    test_type_str = os.getenv(EnumTestKeys.TYPE.value) or EnumTestTypes.MANDATORY.value
    test_type = EnumTestTypes(test_type_str)

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
                     get_publications_response,
                     ):
        delete_json = process_client.delete_workspace_publications(publ_type, self.owner, actor_name=actor_name)
        publication_set = {publication['name'] for publication in delete_json}
        assert after_delete_publications == publication_set
        exp_response_keys = {'name', 'title', 'uuid', 'access_rights', 'url'}
        for delete_json_item in delete_json:
            assert set(delete_json_item.keys()) == exp_response_keys, f'{delete_json_item=}\n{exp_response_keys=}'
            publ_info_response = next(iter(info for info in get_publications_response if info['name'] == delete_json_item['name']))
            for key in exp_response_keys:
                assert delete_json_item[key] == publ_info_response[key]

        get_json = process_client.get_publications(publ_type, workspace=self.owner,
                                                   actor_name=self.owner)
        publication_set = {publication['name'] for publication in get_json}
        assert remaining_publications == publication_set

    publ_types_for_test_type = [process_client.LAYER_TYPE, process_client.MAP_TYPE]
    available_write_rights_for_test_type = [
        pytest.param(f'{owner},{deleter}', id='access_by_user'),
        pytest.param(f'{owner},{ROLE}', id='access_by_role'),
    ]

    if test_type == EnumTestTypes.OPTIONAL:
        publ_types_for_test_type = process_client.PUBLICATION_TYPES
        available_write_rights_for_test_type += [pytest.param('EVERYONE', id='access_by_everyone')]

    @pytest.mark.parametrize('publ_type', publ_types_for_test_type)
    @pytest.mark.parametrize('available_write_rights', available_write_rights_for_test_type)
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
            process_client.publish_workspace_publication(publ_type, owner, name,
                                                         access_rights=access_rights,
                                                         actor_name=owner)

        response = process_client.get_publications(publ_type, workspace=owner, actor_name=owner)
        assert len(response) == len(publications)

        # Delete by other user with rights only for one layer
        self.check_delete(self.deleter,
                          {publication_b, },
                          {publication_a, },
                          publ_type,
                          response,
                          )

        # Delete by owner, everything is deleted
        self.check_delete(owner,
                          {publication_a, },
                          set(),
                          publ_type,
                          response,
                          )
