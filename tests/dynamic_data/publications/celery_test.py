import time
import pytest

from layman import app, celery
from layman.common import empty_method_returns_true
from test_tools import process_client
from tests.asserts import processing
from tests.asserts.final.publication import internal


@pytest.mark.usefixtures('ensure_layman_module')
def test_task_abortion():
    workspace = 'test_task_abortion_ws'
    layername = 'test_task_abortion_layer'

    post_response = process_client.publish_workspace_publication(process_client.LAYER_TYPE,
                                                                 workspace, layername,
                                                                 file_paths=[
                                                                     'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson', ],
                                                                 check_response_fn=empty_method_returns_true,
                                                                 raise_if_not_complete=False,
                                                                 )
    processing.response.valid_post(workspace, process_client.LAYER_TYPE, layername, post_response)
    time.sleep(2)
    with app.app_context():
        celery.abort_publication_chain(workspace,
                                       process_client.LAYER_TYPE,
                                       layername,
                                       )
    internal.expected_chain_info_state(workspace, process_client.LAYER_TYPE, layername, 'ABORTED')
    process_client.delete_workspace_layer(workspace, layername)
