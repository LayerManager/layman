from layman.util import XForwardedClass
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import rest as assert_rest
from tests.dynamic_data import base_test, base_test_classes
from tests.dynamic_data.publications import common_publications
from test_tools import assert_util

pytest_generate_tests = base_test.pytest_generate_tests


class PublicationTypes(base_test_classes.PublicationByDefinitionBase):
    LAYER = (common_publications.LAYER_VECTOR_SLD, 'layer')
    MAP = (common_publications.MAP_EMPTY, 'map')


class TestPublication(base_test.TestSingleRestPublication):
    workspace = 'x_forwarded_prefix_post_workspace'
    publication_type = None

    rest_parametrization = [
        base_test_classes.RestMethodAll,
        PublicationTypes,
    ]

    test_cases = [base_test.TestCaseType(key='proxy_test',
                                         publication=lambda publ_def, cls: Publication(cls.workspace,
                                                                                       publ_def.type,
                                                                                       None),
                                         type=EnumTestTypes.MANDATORY,
                                         )]

    def test_publication(self, publication, rest_method):
        x_forwarded_items = XForwardedClass(proto='https', host='localhost:4142', prefix='/layman-proxy')
        response = rest_method.fn(publication, args={'headers': x_forwarded_items.headers})
        publication_response = response[0] if isinstance(response, list) and len(response) == 1 else response
        geodata_type = publication_response.get('geodata_type')
        exp_resp = assert_rest.get_expected_urls_in_rest_response(publication.workspace, publication.type, publication.name,
                                                                  rest_method=rest_method.enum_item.publ_name_part,
                                                                  x_forwarded_items=x_forwarded_items,
                                                                  geodata_type=geodata_type,
                                                                  )

        assert_util.assert_same_values_for_keys(
            expected=exp_resp,
            tested=publication_response,
        )
