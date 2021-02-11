import pytest
import os

from layman import app, settings
from layman.layer import qgis
from layman.layer.qgis import wms
from test import process_client


@pytest.mark.usefixtures('ensure_layman')
def test_qgis_rest():
    workspace = 'test_qgis_rest_workspace'
    layer = 'test_qgis_rest_layer'
    workspace_directory = f'{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}'
    layer_directory = f'{workspace_directory}/layers/{layer}'

    assert not os.path.exists(workspace_directory)
    assert not os.path.exists(layer_directory)

    process_client.publish_layer(workspace, layer)
    assert os.path.exists(workspace_directory)
    assert os.path.exists(layer_directory)
    with app.app_context():
        assert wms.get_layer_info(workspace, layer) == {'name': layer}
        assert workspace in qgis.get_workspaces()

    process_client.delete_layer(workspace, layer)
    assert os.path.exists(workspace_directory)
    assert not os.path.exists(layer_directory)
    with app.app_context():
        assert wms.get_layer_info(workspace, layer) == {}
        assert workspace in qgis.get_workspaces()
