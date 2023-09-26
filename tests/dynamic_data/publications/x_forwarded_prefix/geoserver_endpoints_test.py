import pytest
from layman.util import XForwardedClass
from test_tools import geoserver_client

X_FORWARDED_ITEMS = XForwardedClass(proto='https', host='localhost:4143', prefix='/layman-proxy')
headers = {**X_FORWARDED_ITEMS.headers,
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
    assert all(m.get('url').startswith(f'https://localhost:4143/layman-proxy/geoserver/')
               for operation in ['GetCapabilities', 'GetMap', 'GetFeatureInfo']
               for m in wms_inst.getOperationByName(operation).methods
               ), f"{wms_inst.getServiceXML()}"


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
    assert all(m.get('url').startswith(f'https://localhost:4143/layman-proxy/geoserver/')
               for operation in ['GetCapabilities', 'DescribeFeatureType', 'GetFeature']
               for m in wfs_inst.getOperationByName(operation).methods
               ), f"{getattr(wfs_inst, '_capabilities')}"
