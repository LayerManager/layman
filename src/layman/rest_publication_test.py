import pytest
import json

from test import process, process_client

ensure_layman = process.ensure_layman


@pytest.mark.parametrize("publish_method, patch_method, delete_method", [
    (process_client.publish_layer, process_client.patch_layer, process_client.delete_layer,),
    (process_client.publish_map, process_client.patch_map, process_client.delete_map,),
])
@pytest.mark.usefixtures('ensure_layman')
def test_wrong_post(publish_method,
                    patch_method,
                    delete_method):
    def check_response(resp):
        assert resp.status_code == 400, (resp.status_code, r.text)
        resp_json = json.loads(resp.text)
        assert resp_json['code'] == 43, (resp.status_code, resp.text)
        assert resp_json['message'] == 'Wrong access rights.', (resp.status_code, resp.text)

    workspace = 'test_wrong_post_workspace'
    publication = 'test_wrong_post_publication'

    r = publish_method(workspace, publication, access_rights={'read': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = publish_method(workspace, publication, access_rights={'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = publish_method(workspace, publication, access_rights={'read': 'EVRBODY', 'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    publish_method(workspace, publication)

    r = patch_method(workspace, publication, access_rights={'read': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = patch_method(workspace, publication, access_rights={'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = patch_method(workspace, publication, access_rights={'read': 'EVRBODY', 'write': 'EVRBODY'}, assert_status=False)
    check_response(r)

    r = patch_method(workspace, publication)

    delete_method(workspace, publication)
