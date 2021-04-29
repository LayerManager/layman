import os
from test import process_client
from test.util import url_for
import pytest

from layman import app, settings
from layman.layer import qgis
from layman.layer.qgis import wms


@pytest.mark.usefixtures('ensure_layman')
def test_qgis_rest():
    workspace = 'test_qgis_rest_workspace'
    layer = 'test_qgis_rest_workspace_layer'
    source_style_file_path = 'sample/style/small_layer.qml'
    workspace_directory = f'{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}'
    layer_directory = f'{workspace_directory}/layers/{layer}'

    assert not os.path.exists(workspace_directory)
    assert not os.path.exists(layer_directory)

    process_client.publish_workspace_layer(workspace,
                                           layer,
                                           style_file=source_style_file_path)
    assert os.path.exists(workspace_directory)
    assert os.path.exists(layer_directory)
    with app.app_context():
        url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=layer, internal=False)
        assert wms.get_layer_info(workspace, layer) == {'name': layer,
                                                        'style': {'type': 'qml',
                                                                  'url': url},
                                                        }
        assert workspace in qgis.get_workspaces()

    process_client.delete_workspace_layer(workspace, layer)
    assert os.path.exists(workspace_directory)
    assert not os.path.exists(layer_directory)
    with app.app_context():
        assert wms.get_layer_info(workspace, layer) == {}
        assert workspace in qgis.get_workspaces()
