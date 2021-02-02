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
    style_file = 'sample/style/generic-blue.xml'
    expected_file = 'sample/style/test_sld_style_applied_in_thumbnail_layer.png'

    process_client.publish_layer(workspace,
                                 layer,
                                 file_paths=geojson_file,
                                 style_file=style_file)

    with app.app_context():
        thumbnail_path = thumbnail.get_layer_thumbnail_path(workspace, layer)

    diffs = util.compare_images(expected_file, thumbnail_path)

    assert diffs < 1000

    process_client.delete_layer(workspace,
                                layer)
