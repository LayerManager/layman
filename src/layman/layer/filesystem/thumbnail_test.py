import pytest

from test_tools import process_client

headers_sld = {
    'Accept': 'application/vnd.ogc.sld+xml',
    'Content-type': 'application/xml',
}


@pytest.mark.usefixtures('ensure_layman')
def test_wrong_sld_causes_no_thumbnail():
    workspace = 'test_wrong_sld_causes_no_thumbnail_workspace'
    layer = 'test_wrong_sld_causes_no_thumbnail_layer'
    geojson_file = ['/code/sample/layman.layer/sample_point_cz.geojson']
    style_file = '/code/sample/layman.layer/sample_point_cz_wrong_literal.sld'

    def wait_for_thumbnail_error(response):
        ok_keys = ['db', 'wms', 'wfs', 'file']
        if response.status_code == 200:
            r_json = response.json()
            result = response.status_code == 200 and all(
                'status' not in r_json[k] for k in ok_keys
            ) and 'status' in r_json['thumbnail'] and r_json['thumbnail']['status'] in ['FAILURE']
        else:
            result = False
        return result

    process_client.publish_workspace_layer(workspace,
                                           layer,
                                           file_paths=geojson_file,
                                           style_file=style_file,
                                           check_response_fn=wait_for_thumbnail_error,
                                           raise_if_not_complete=False,
                                           )

    layer_info = process_client.get_workspace_layer(workspace, layer)

    assert 'error' in layer_info['thumbnail']
    assert layer_info['thumbnail']['error']['message'] == 'Thumbnail rendering failed'
    assert layer_info['thumbnail']['error']['code'] == -1

    process_client.delete_workspace_layer(workspace,
                                          layer)
