import pytest
from test_tools import geoserver_client


@pytest.mark.parametrize('version', [
    '1.3.0',
    '1.1.1'
])
@pytest.mark.usefixtures('ensure_layman_module')
def test_wms_get_capabilities(version):
    proxy_prefix = '/layman-proxy'
    headers = {'X-Forwarded-Prefix': proxy_prefix,
               'X-Forwarded-Path': '/some-other-proxy',
               }
    wms_inst = geoserver_client.get_wms_capabilities(workspace=None,
                                                     version=version,
                                                     headers=headers,
                                                     )
    assert all(m.get('url').startswith(f'http://localhost:8000{proxy_prefix}/geoserver/') for operation in
               ['GetCapabilities', 'GetMap', 'GetFeatureInfo'] for m in wms_inst.getOperationByName(operation).methods)
