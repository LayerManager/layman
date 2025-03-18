import pytest

from test_tools import process_client
from geoserver import util as gs_util
from layman import app, settings
from layman.layer.layer_class import Layer


@pytest.mark.usefixtures('ensure_layman_module')
def test_issue_738():
    workspace = 'dynamic_test_workspace_layer_issue_738'
    layername = 'layer_issue_738'

    #  Publish with sld 1.0.0 style
    process_client.publish_workspace_layer(workspace=workspace,
                                           name=layername,
                                           style_file='sample/style/basic.sld',
                                           )
    with app.app_context():
        layer = Layer(layer_tuple=(workspace, layername))
    style_name = layer.gs_ids.sld

    response = gs_util.get_workspace_style_response(geoserver_workspace=style_name.workspace,
                                                    stylename=style_name.name,
                                                    headers=gs_util.headers_sld['1.1.0'],
                                                    auth=settings.LAYMAN_GS_AUTH,
                                                    )
    style = response.content.decode()
    assert 'StyledLayerDescriptorImpl@' in style

    process_client.delete_workspace_layer(workspace=workspace, name=layername)
