import pytest

from layman import LaymanError
from test_tools import process_client, role_service as role_service_util
from tests import EnumTestTypes
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test, base_test_classes
from tests.dynamic_data.publications import common_publications

pytest_generate_tests = base_test.pytest_generate_tests


class PublicationTypes(base_test_classes.PublicationByDefinitionBase):
    LAYER = (common_publications.LAYER_VECTOR_SLD, 'layer')


OWNER = 'test_role_application_user'
ROLE = 'TEST_ROLE_APPLICATION_ROLE'
ROLE_USER = 'test_role_application_role_user'
USERS_AND_ROLES = {OWNER, ROLE}


@pytest.mark.usefixtures('oauth2_provider_mock')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = OWNER
    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
    ]

    usernames_to_reserve = [
        OWNER,
        ROLE_USER,
    ]

    test_cases = [base_test.TestCaseType(key='role_test',
                                         rest_args={
                                             'access_rights': {
                                                 'read': ','.join(USERS_AND_ROLES),
                                             },
                                             'actor_name': OWNER,
                                         },
                                         type=EnumTestTypes.MANDATORY,
                                         )]

    def test_publication(self, layer, rest_method, rest_args):
        rest_method.fn(layer, args=rest_args)
        assert_util.is_publication_valid_and_complete(layer)

        with pytest.raises(LaymanError) as exc_info:
            process_client.get_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=ROLE_USER)
        assert exc_info.value.http_code == 404
        assert exc_info.value.code == 15
        assert exc_info.value.message == 'Layer was not found'

        role_service_util.ensure_user_role(ROLE_USER, ROLE)
        info = process_client.get_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=ROLE_USER)
        assert set(info['access_rights']['read']) == USERS_AND_ROLES

        role_service_util.delete_user_role(ROLE_USER, ROLE)
        role_service_util.delete_role(ROLE)
