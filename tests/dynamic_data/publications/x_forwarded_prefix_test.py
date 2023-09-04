from layman import settings
from test_tools import process_client
from tests import EnumTestTypes
from tests.dynamic_data import base_test, base_test_classes
from tests.dynamic_data.publications import common_publications
from ... import Publication

pytest_generate_tests = base_test.pytest_generate_tests


class RestMethodLocal(base_test_classes.RestMethodBase):
    POST = ('post_publication', 'post')
    DELETE = ('delete_workspace_publication', 'delete')
    MULTI_DELETE = ('delete_workspace_publications', 'multi_delete')


class PublicationTypes(base_test_classes.PublicationByDefinitionBase):
    LAYER = (common_publications.LAYER_VECTOR_SLD, 'layer')
    MAP = (common_publications.MAP_EMPTY, 'map')


class TestPublication(base_test.TestSingleRestPublication):
    workspace = 'x_forwarded_prefix_post_workspace'
    publication_type = None

    rest_parametrization = [
        RestMethodLocal,
        PublicationTypes,
    ]

    test_cases = [base_test.TestCaseType(key='proxy_test',
                                         publication=lambda publ_def, cls: Publication(cls.workspace,
                                                                                       publ_def.type,
                                                                                       None),
                                         type=EnumTestTypes.MANDATORY,
                                         specific_types={
                                             (PublicationTypes.MAP, RestMethodLocal.POST): EnumTestTypes.IGNORE,
                                         },
                                         )]

    @classmethod
    def delete_workspace_publication(cls, publication, args=None):
        return process_client.delete_workspace_publication(publication.type, publication.workspace, publication.name, **args)

    @classmethod
    def delete_workspace_publications(cls, publication, args=None):
        return process_client.delete_workspace_publications(publication.type, publication.workspace, **args)

    @staticmethod
    def test_publication(publication, rest_method):
        proxy_prefix = '/layman-proxy'
        response = rest_method(publication, args={'headers': {'X-Forwarded-Prefix': proxy_prefix}})
        publication_response = response[0] if isinstance(response, list) and len(response) == 1 else response
        assert publication_response['url'] == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/{publication.type.split(".")[1]}s/{publication.name}'
