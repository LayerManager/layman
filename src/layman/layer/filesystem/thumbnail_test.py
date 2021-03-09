import pytest
from layman import app
from . import thumbnail
from test import process_client, util


headers_sld = {
    'Accept': 'application/vnd.ogc.sld+xml',
    'Content-type': 'application/xml',
}


@pytest.mark.usefixtures('ensure_layman')
def test_sld_style_applied_in_thumbnail():
    workspace = 'test_sld_style_applied_in_thumbnail_workspace'
    layer = 'test_sld_style_applied_in_thumbnail_layer'
    geojson_file = ['/code/tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson']
    style_file = 'sample/style/generic-blue_sld.xml'
    expected_file = 'sample/style/test_sld_style_applied_in_thumbnail_layer.png'

    process_client.publish_workspace_layer(workspace,
                                           layer,
                                           file_paths=geojson_file,
                                           style_file=style_file)

    with app.app_context():
        thumbnail_path = thumbnail.get_layer_thumbnail_path(workspace, layer)

    diffs = util.compare_images(expected_file, thumbnail_path)

    assert diffs < 1000

    process_client.delete_workspace_layer(workspace,
                                          layer)


@pytest.mark.usefixtures('ensure_layman')
def test_wrong_sld_causes_no_thumbnail():
    workspace = 'test_wrong_sld_causes_no_thumbnail_workspace'
    layer = 'test_wrong_sld_causes_no_thumbnail_layer'
    geojson_file = ['/code/sample/layman.layer/sample_point_cz.geojson']
    style_file = '/code/sample/layman.layer/sample_point_cz_wrong_literal.sld'

    def wait_for_thumbnail_error(response):
        ok_keys = ['db_table', 'wms', 'wfs', 'file']
        if response.status_code == 200:
            r_json = response.json()
            return response.status_code == 200 and all(
                'status' not in r_json[k] for k in ok_keys
            ) and 'status' in r_json['thumbnail'] and r_json['thumbnail']['status'] in ['FAILURE']
        else:
            return False

    process_client.publish_workspace_layer(workspace,
                                           layer,
                                           file_paths=geojson_file,
                                           style_file=style_file,
                                           check_response_fn=wait_for_thumbnail_error,
                                           )

    layer_info = process_client.get_workspace_layer(workspace, layer)

    assert 'error' in layer_info['thumbnail']
    assert layer_info['thumbnail']['error']['message'] == 'Thumbnail rendering failed'
    assert layer_info['thumbnail']['error']['code'] == -1

    process_client.delete_workspace_layer(workspace,
                                          layer)
