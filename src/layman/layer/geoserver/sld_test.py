import pytest
import requests

from urllib.parse import urljoin

from layman import settings
from test import process_client, util

headers_sld = {
    'Accept': 'application/vnd.ogc.sld+xml',
    'Content-type': 'application/xml',
}


@pytest.mark.usefixtures('ensure_layman')
@pytest.mark.xfail(reason='Not implemented yet')
def test_sld_style_in_wms_workspace():
    workspace = 'test_sld_style_file_workspace'
    layer = 'test_sld_style_file_layer'
    geojson_file = ['/code/tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson']
    style_file = 'sample/style/generic-blue.xml'

    process_client.publish_layer(workspace,
                                 layer,
                                 file_paths=geojson_file,
                                 style_file=style_file)

    url = urljoin(settings.LAYMAN_GS_REST, f'workspaces/{workspace}_wms/styles/{layer}')

    r = requests.get(url,
                     auth=settings.LAYMAN_GS_AUTH,
                     headers=headers_sld,
                     timeout=5,
                     )
    r.raise_for_status()
    process_client.delete_layer(workspace,
                                layer)


