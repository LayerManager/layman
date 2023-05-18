import sys
import requests
import pytest

del sys.modules['layman']

from layman import app, settings, LaymanError, util as layman_util
from layman.layer import util as layer_util
from layman.layer.filesystem import input_style
from test_tools import process_client, util as test_util
from test_tools.util import url_for
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman')
def test_get_layer_title():
    workspace = 'test_get_layer_title_workspace'
    layers = [("c_test_get_layer_title_layer", "C Test get layer title - map layer íářžý"),
              ("a_test_get_layer_title_layer", "A Test get layer title - map layer íářžý"),
              ("b_test_get_layer_title_layer", "B Test get layer title - map layer íářžý")
              ]
    sorted_layers = sorted(layers)

    for (name, title) in layers:
        process_client.publish_workspace_layer(workspace, name, title=title)

    # layers.GET
    with app.app_context():
        url = url_for('rest_workspace_layers.get', workspace=workspace)
    response = requests.get(url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.text

    for i in range(0, len(sorted_layers) - 1):
        assert response.json()[i]["name"] == sorted_layers[i][0]
        assert response.json()[i]["title"] == sorted_layers[i][1]

    for (name, title) in layers:
        process_client.delete_workspace_layer(workspace, name)


def assert_style_file(workspace,
                      layer,
                      expected_style_file):
    with app.app_context():
        style_file_path = input_style.get_file_path(workspace, layer)
        layer_style_file = input_style.get_layer_file(workspace, layer)
    assert style_file_path == expected_style_file or all(v is None for v in [style_file_path, expected_style_file])
    assert all(v is not None for v in [layer_style_file, expected_style_file])\
        or all(v is None for v in [layer_style_file, expected_style_file])


@pytest.mark.parametrize('source_style_file_path, layer_suffix, expected_style_file_template, expected_style_type', [
    ('sample/style/generic-blue_sld.xml', '_sld', '/layman_data_test/workspaces/{workspace}/layers/{layer}/input_style/{layer}.sld', 'sld'),
    ('sample/style/sld_1_1_0.xml', '_sld11', '/layman_data_test/workspaces/{workspace}/layers/{layer}/input_style/{layer}.sld', 'sld'),
    ('sample/style/small_layer.qml', '_qml', '/layman_data_test/workspaces/{workspace}/layers/{layer}/input_style/{layer}.qml', 'qml'),
    ('', '_no_style', None, 'sld'),
])
@pytest.mark.usefixtures('ensure_layman')
def test_style_correctly_saved(source_style_file_path,
                               layer_suffix,
                               expected_style_file_template,
                               expected_style_type):
    workspace = 'test_style_correctly_saved_workspace'
    layer = 'test_style_correctly_saved_layer' + layer_suffix
    expected_style_file = expected_style_file_template.format(workspace=workspace, layer=layer) if expected_style_file_template else None
    process_client.publish_workspace_layer(workspace,
                                           layer,
                                           style_file=source_style_file_path)
    assert_style_file(workspace, layer, expected_style_file)
    with app.app_context():
        info = layman_util.get_publication_info(workspace, process_client.LAYER_TYPE, layer, context={'keys': ['style_type', 'style'], })
    assert info['_style_type'] == expected_style_type

    process_client.delete_workspace_layer(workspace, layer)
    process_client.publish_workspace_layer(workspace, layer)

    with app.app_context():
        info = layer_util.get_layer_info(workspace, layer)
    assert info['_style_type'] == 'sld'
    assert info['style']['type'] == 'sld', info.get('style')
    assert info['style']['url'], info.get('style')

    assert_style_file(workspace, layer, None)

    process_client.patch_workspace_layer(workspace,
                                         layer,
                                         style_file=source_style_file_path)
    assert_style_file(workspace, layer, expected_style_file)
    with app.app_context():
        info = layer_util.get_layer_info(workspace, layer)
    assert info['_style_type'] == expected_style_type

    process_client.delete_workspace_layer(workspace, layer)


@pytest.mark.parametrize('post_params, expected_exc', [
    ({'file_paths': ['sample/layman.layer/sample_tif_rgb.tif', ],
      'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
      },
     {'http_code': 400,
      'code': 48,
      'message': 'Wrong combination of parameters',
      'data': 'Raster layers are not allowed to have QML style.',
      },
     )
])
@pytest.mark.usefixtures('ensure_layman')
def test_error(post_params, expected_exc):
    workspace = 'test_error_workspace'
    layer = 'test_error_layer'

    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_layer(workspace, layer, **post_params)
    test_util.assert_error(expected_exc, exc_info)
