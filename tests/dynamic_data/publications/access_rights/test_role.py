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
USERS_AND_ROLES = {USERNAME, 'ROLE1', 'EVERYONE'}


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
                                                 'read': ','.join(USERS_AND_ROLES),
                                             }
                                         },
                                         type=EnumTestTypes.MANDATORY,
                                         )]

    def test_publication(self, publication, rest_method, rest_args):
        rest_method.fn(publication, args=rest_args)
        assert_util.is_publication_valid_and_complete(publication)
        info = process_client.get_workspace_publication(publication.type, publication.workspace, publication.name)
        assert set(info['access_rights']['read']) == USERS_AND_ROLES
