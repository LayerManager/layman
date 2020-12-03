import pytest
import json

from test import process, process_client

ensure_layman = process.ensure_layman


@pytest.mark.parametrize("publish_method, delete_method", [
    (process_client.publish_layer, process_client.delete_layer,),
    (process_client.publish_map, process_client.delete_map,),
])
@pytest.mark.usefixtures('ensure_layman')
def test_wrong_post(publish_method,
                    delete_method):
    workspace = 'test_wrong_post_workspace'
    publication = 'test_wrong_post_publication'

    r = publish_method(workspace, publication, access_rights={'read': 'EVRBODY'}, assert_status=False)
    assert r.status_code == 400, (r.status_code, r.text)
    resp_json = json.loads(r.text)
    assert resp_json['code'] == 43, (r.status_code, r.text)
    assert resp_json['message'] == 'Wrong access rights.', (r.status_code, r.text)

    publish_method(workspace, publication)

    delete_method(workspace, publication)
