import copy
import pytest

from geoserver.error import Error as gs_error
from layman import settings
from layman.layer.geoserver import GEOSERVER_WFS_WORKSPACE
from tests import Publication4Test, EnumTestTypes
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test
from tests.dynamic_data.publications import common_publications as publications
from test_tools import process_client, wfs_client

pytest_generate_tests = base_test.pytest_generate_tests
WORKSPACE = 'geoserver_proxy_wfs_test_ws'
USER = 'geoserver_proxy_wfs_authz_test_user'
USER_2 = 'geoserver_proxy_wfs_authz_test_user_2'

PUBLIC_LAYER = Publication4Test(WORKSPACE, process_client.LAYER_TYPE, 'geoserver_proxy_wfs_test_public_layer', uuid='cab68845-7f33-44a2-8696-c55b7ca03393')
PRIVATE_LAYER = Publication4Test(USER, process_client.LAYER_TYPE, 'geoserver_proxy_wfs_test_private_layer', uuid='a97b78b9-f92b-4ed9-9eac-fea775f1bf48')

OK_TEST_CASES = {
    'public_layer_specific_url': {
        'layer': PUBLIC_LAYER,
        'wfs_params': {
            'request_workspace': GEOSERVER_WFS_WORKSPACE,
        },
    },
    'public_layer_generic_url': {
        'layer': PUBLIC_LAYER,
        'wfs_params': {
        },
    },
    'private_layer_specific_url': {
        'layer': PRIVATE_LAYER,
        'wfs_params': {
            'request_workspace': GEOSERVER_WFS_WORKSPACE,
            'request_headers': process_client.get_authz_headers(username=USER),
        },
    },
    'private_layer_generic_url': {
        'layer': PRIVATE_LAYER,
        'wfs_params': {
            'request_headers': process_client.get_authz_headers(username=USER),
        },
    },
}

ERROR_TEST_CASES = {
    'private_layer_specific_url_unauthz_user': {
        'layer': PRIVATE_LAYER,
        'wfs_params': {
            'request_workspace': GEOSERVER_WFS_WORKSPACE,
            'request_headers': process_client.get_authz_headers(username=USER_2),
        },
    },
    'private_layer_generic_url_unauthz_user': {
        'layer': PRIVATE_LAYER,
        'wfs_params': {
            'request_headers': process_client.get_authz_headers(username=USER_2),
        },
    },
    'private_layer_specific_url_no_user': {
        'layer': PRIVATE_LAYER,
        'wfs_params': {
            'request_workspace': GEOSERVER_WFS_WORKSPACE,
        },
    },
    'private_layer_generic_url_no_user': {
        'layer': PRIVATE_LAYER,
        'wfs_params': {
        },
    },
    'private_layer_generic_url_fraud_header': {
        'layer': PRIVATE_LAYER,
        'wfs_params': {
            'request_headers': {settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: USER, },
        },
    },
}


@pytest.mark.usefixtures('oauth2_provider_mock')
class TestWfsProxyOkCall(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.LAYER_TYPE
    rest_parametrization = []
    usernames_to_reserve = [USER, USER_2]

    test_cases = [
        base_test.TestCaseType(
            key=key,
            publication=params['layer'],
            type=EnumTestTypes.MANDATORY,
            params=copy.deepcopy(params),
        ) for key, params in OK_TEST_CASES.items()
    ]

    def before_class(self):
        self.post_publication(PUBLIC_LAYER, args=publications.SMALL_LAYER.definition, scope='class')
        self.post_publication(PRIVATE_LAYER, args={'actor_name': USER, **publications.SMALL_LAYER.definition}, scope='class',)

    def test_wfs_proxy(self, layer: Publication4Test, params):
        wfs_client.post_wfst(*layer,
                             operation=wfs_client.WfstOperation.INSERT,
                             version=wfs_client.WfstVersion.WFS20,
                             **params['wfs_params'],
                             )
        assert_util.is_publication_valid_and_complete(layer)


@pytest.mark.usefixtures('oauth2_provider_mock')
class TestWfsProxyErrorCall(base_test.TestSingleRestPublication):
    workspace = USER
    publication_type = process_client.LAYER_TYPE
    rest_parametrization = []
    usernames_to_reserve = [USER, USER_2]

    test_cases = [
        base_test.TestCaseType(
            key=key,
            publication=params['layer'],
            type=EnumTestTypes.MANDATORY,
            params=copy.deepcopy(params),
        ) for key, params in ERROR_TEST_CASES.items()
    ]

    def before_class(self):
        self.post_publication(PRIVATE_LAYER, args={'actor_name': USER, **publications.SMALL_LAYER.definition}, scope='class',)

    def test_wfs_proxy(self, layer: Publication4Test, params):
        with pytest.raises(gs_error) as raised_gs_error:
            wfs_client.post_wfst(*layer,
                                 operation=wfs_client.WfstOperation.INSERT,
                                 version=wfs_client.WfstVersion.WFS20,
                                 **params['wfs_params'],
                                 )
        assert raised_gs_error.value.code == -1, f"{raised_gs_error=}, {raised_gs_error.code=}"
        assert raised_gs_error.value.message == "WFS-T error", f"{raised_gs_error=}, {raised_gs_error.message=}"
        assert raised_gs_error.value.data == {'status_code': 400}, f"{raised_gs_error=}, {raised_gs_error.data=}"
        assert_util.is_publication_valid_and_complete(layer)
