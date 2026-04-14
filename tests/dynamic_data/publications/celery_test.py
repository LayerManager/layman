import time
import pytest

from layman import app
from layman.layer import util as layer_util
from layman.common import empty_method_returns_true
from test_tools import process_client
from tests.asserts import processing
from tests.asserts.final.publication import internal


@pytest.mark.usefixtures('ensure_layman_module')
def test_task_abortion():
    workspace = 'test_task_abortion_ws'
    layername = 'test_task_abortion_layer'

    post_response = process_client.publish_publication(process_client.LAYER_TYPE,
                                                       workspace, layername,
                                                       file_paths=[
                                                           'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson', ],
                                                       check_response_fn=empty_method_returns_true,
                                                       raise_if_not_complete=False,
                                                       )
    processing.response.valid_post(process_client.LAYER_TYPE, layername, post_response)
    time.sleep(2)
    layer_uuid = post_response['uuid']
    with app.app_context():
        layer_util.abort_layer_chain_by_uuid(layer_uuid)
    internal.expected_chain_info_state_by_uuid(layer_uuid, 'ABORTED')
    process_client.delete_layer(layer_uuid)
