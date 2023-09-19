from lxml import etree as ET
import requests
import pytest

from geoserver import util as gs_util
from micka import NAMESPACES
from test_tools import process_client
from tests import Publication
from tests.dynamic_data import base_test


@pytest.mark.xfail(reason="Geoserver removes default values.")
class TestPublication(base_test.TestSingleRestPublication):
    workspace = 'dynamic_test_workspace_sld_wellknownname'
    publication_type = process_client.LAYER_TYPE
    layername = 'layer_sld_wellknownname'

    def test_sld_wellknownname(self, ):
        self.post_publication(Publication(self.workspace, self.publication_type, self.layername))
        response = requests.get(
            gs_util.get_workspace_style_url(self.workspace + '_wms', self.layername),
            auth=gs_util.GS_AUTH,
            headers=gs_util.headers_sld['1.0.0'],
            timeout=gs_util.GS_REST_TIMEOUT,
        )
        parser = ET.XMLParser(remove_blank_text=True)
        resp_tree = ET.fromstring(response.content, parser=parser)
        response_wkn = resp_tree.xpath('//sld:WellKnownName', namespaces=NAMESPACES)
        assert len(response_wkn) == 1, f'{ET.tostring(resp_tree, encoding="unicode", pretty_print=True)}'
        response_wkn = response_wkn[0]
        assert response_wkn.text == 'square'
