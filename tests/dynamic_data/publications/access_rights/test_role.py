import pytest

from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test, base_test_classes
from tests.dynamic_data.publications import common_publications

pytest_generate_tests = base_test.pytest_generate_tests


class PublicationTypes(base_test_classes.PublicationByDefinitionBase):
    LAYER = (common_publications.LAYER_VECTOR_SLD, 'layer')
    MAP = (common_publications.MAP_EMPTY, 'map')


USERNAME = 'test_access_rights_role_user1'
USER_ROLE1_ROLE3_EVERYONE = {USERNAME, 'ROLE1', 'ROLE3', 'EVERYONE'}
USER_ROLE1 = {USERNAME, 'ROLE1'}
USER_ROLE1_ROLE2 = {USERNAME, 'ROLE1', 'ROLE2'}


@pytest.mark.usefixtures('oauth2_provider_mock')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = 'test_access_rights_role'
    publication_type = None

    rest_parametrization = [
        PublicationTypes,
        base_test_classes.RestMethod
    ]

    usernames_to_reserve = [
        USERNAME,
    ]

    test_cases = [base_test.TestCaseType(key='role_test',
                                         publication=lambda publ_def, cls: Publication(cls.workspace,
                                                                                       publ_def.type,
                                                                                       None),
                                         rest_args={
                                             'access_rights': {
                                                 'read': ','.join(USER_ROLE1_ROLE2),
                                                 'write': ','.join(USER_ROLE1),
                                             },
                                             'actor_name': USERNAME,
                                         },
                                         post_before_test_args={
                                             'access_rights': {
                                                 'read': ','.join(USER_ROLE1_ROLE3_EVERYONE),
                                             }
                                         },
                                         type=EnumTestTypes.MANDATORY,
                                         )]

    def test_publication(self, publication, rest_method, rest_args):
        if rest_method.enum_item == base_test_classes.RestMethod.PATCH:
            info = process_client.get_workspace_publication(publication.type, publication.workspace, publication.name)
            assert set(info['access_rights']['read']) == USER_ROLE1_ROLE3_EVERYONE
            assert set(info['access_rights']['write']) == {'EVERYONE'}

        rest_method.fn(publication, args=rest_args)
        assert_util.is_publication_valid_and_complete(publication)

        info = process_client.get_workspace_publication(publication.type, publication.workspace, publication.name,
                                                        actor_name=USERNAME)
        assert set(info['access_rights']['read']) == USER_ROLE1_ROLE2
        assert set(info['access_rights']['write']) == USER_ROLE1
