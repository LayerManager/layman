import pytest
from test_tools import geoserver_client

PROXY_PREFIX = '/layman-proxy'
headers = {'X-Forwarded-Prefix': PROXY_PREFIX,
           'X-Forwarded-Path': '/some-other-proxy',
           }


@pytest.mark.parametrize('version', [
    '1.3.0',
    '1.1.1'
])
@pytest.mark.usefixtures('ensure_layman_module')
def test_wms_get_capabilities(version):
    wms_inst = geoserver_client.get_wms_capabilities(workspace=None,
                                                     version=version,
                                                     headers=headers,
                                                     )
    assert all(m.get('url').startswith(f'http://localhost:8000{PROXY_PREFIX}/geoserver/') for operation in
               ['GetCapabilities', 'GetMap', 'GetFeatureInfo'] for m in wms_inst.getOperationByName(operation).methods)


@pytest.mark.parametrize('version', [
    '2.0.0',
    '1.1.0'
])
@pytest.mark.usefixtures('ensure_layman_module')
def test_wfs_get_capabilities(version):
    wfs_inst = geoserver_client.get_wfs_capabilities(workspace=None,
                                                     version=version,
                                                     headers=headers,
                                                     )
    assert all(m.get('url').startswith(f'http://localhost:8000{PROXY_PREFIX}/geoserver/') for operation in
               ['GetCapabilities', 'DescribeFeatureType', 'GetFeature'] for m in wfs_inst.getOperationByName(operation).methods)
