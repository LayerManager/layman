import pytest

from test_tools import process_client
from geoserver import util as gs_util
from layman import util as laymen_util, app, settings, names


@pytest.mark.usefixtures('ensure_layman_module')
def test_issue_738():
    workspace = 'dynamic_test_workspace_layer_issue_738'
    layer = 'layer_issue_738'

    #  Publish with sld 1.0.0 style
    process_client.publish_workspace_layer(workspace=workspace,
                                           name=layer,
                                           style_file='sample/style/basic.sld',
                                           )
    with app.app_context():
        layer_info = laymen_util.get_publication_info(workspace, process_client.LAYER_TYPE, layer, context={'keys': ['wms', 'uuid']})
    geoserver_workspace = layer_info.get('_wms', {}).get('workspace')
    style_name = names.get_layer_names_by_source(uuid=layer_info['uuid']).sld.name

    response = gs_util.get_workspace_style_response(geoserver_workspace=geoserver_workspace,
                                                    stylename=style_name,
                                                    headers=gs_util.headers_sld['1.1.0'],
                                                    auth=settings.LAYMAN_GS_AUTH,
                                                    )
    style = response.content.decode()
    assert 'StyledLayerDescriptorImpl@' in style

    process_client.delete_workspace_layer(workspace=workspace, name=layer)
