from layman import settings
from tests import EnumTestTypes, Publication
from tests.dynamic_data import base_test, base_test_classes
from tests.dynamic_data.publications import common_publications
from test_tools import assert_util, process_client

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
        proxy_prefix = '/layman-proxy'
        response = rest_method.fn(publication, args={'headers': {'X-Forwarded-Prefix': proxy_prefix}})
        publication_response = response[0] if isinstance(response, list) and len(response) == 1 else response
        if rest_method == self.patch_publication:  # pylint: disable=W0143
            if publication.type == process_client.LAYER_TYPE:
                exp_resp = {
                    'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/{publication.type.split(".")[1]}s/{publication.name}',
                    'thumbnail': {
                        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/layers/{publication.name}/thumbnail'
                    },
                    'metadata': {
                        'comparison_url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/layers/{publication.name}/metadata-comparison',
                    },
                    'wms': {
                        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/geoserver/{publication.workspace}_wms/ows',
                    },
                    'sld': {
                        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/layers/{publication.name}/style',
                    },
                    'style': {
                        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/layers/{publication.name}/style',
                    },
                }

                geodata_type = response['geodata_type']
                if geodata_type == settings.GEODATA_TYPE_VECTOR:
                    exp_resp['wfs'] = {
                        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/geoserver/{publication.workspace}/wfs'
                    }
            else:
                exp_resp = {
                    'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/{publication.type.split(".")[1]}s/{publication.name}',
                    'thumbnail': {
                        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/{publication.type.split(".")[1]}s/{publication.name}/thumbnail'
                    },
                    'file': {
                        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/{publication.type.split(".")[1]}s/{publication.name}/file'
                    },
                    'metadata': {
                        'comparison_url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/{publication.type.split(".")[1]}s/{publication.name}/metadata-comparison',
                    },
                }

        else:
            exp_resp = {'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/{publication.type.split(".")[1]}s/{publication.name}'}

        assert_util.assert_same_values_for_keys(
            expected=exp_resp,
            tested=publication_response,
        )
