import sys
import pytest
import requests
from test import process_client

del sys.modules['layman']

from layman import app, util as layman_util, settings
from layman.layer import util as layer_util
from layman.layer.filesystem import input_style
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman')
def test_get_layer_title():
    username = 'test_get_layer_title_user'
    layers = [("c_test_get_layer_title_layer", "C Test get layer title - map layer íářžý"),
              ("a_test_get_layer_title_layer", "A Test get layer title - map layer íářžý"),
              ("b_test_get_layer_title_layer", "B Test get layer title - map layer íářžý")
              ]
    sorted_layers = sorted(layers)

    for (name, title) in layers:
        process_client.publish_layer(username, name, title=title)

    # layers.GET
    with app.app_context():
        url = layman_util.url_for('rest_layers.get', username=username)
    rv = requests.get(url)
    assert rv.status_code == 200, rv.text

    for i in range(0, len(sorted_layers) - 1):
        assert rv.json()[i]["name"] == sorted_layers[i][0]
        assert rv.json()[i]["title"] == sorted_layers[i][1]

    for (name, title) in layers:
        process_client.delete_layer(username, name)


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
    ('sample/style/generic-blue_sld.xml', '_sld', '/layman_data_test/users/{workspace}/layers/{layer}/input_style/{layer}.sld', 'sld'),
    ('sample/style/sld_1_1_0.xml', '_sld11', '/layman_data_test/users/{workspace}/layers/{layer}/input_style/{layer}.sld', 'sld'),
    ('sample/style/funny_qml.xml', '_qml', '/layman_data_test/users/{workspace}/layers/{layer}/input_style/{layer}.qgis', 'qgis'),
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
    process_client.publish_layer(workspace,
                                 layer,
                                 style_file=source_style_file_path)
    assert_style_file(workspace, layer, expected_style_file)
    with app.app_context():
        info = layer_util.get_layer_info(workspace, layer)
    assert info['style_type'] == expected_style_type

    process_client.delete_layer(workspace, layer)
    process_client.publish_layer(workspace, layer)

    with app.app_context():
        info = layer_util.get_layer_info(workspace, layer)
    assert info['style_type'] == 'sld'

    assert_style_file(workspace, layer, None)

    process_client.patch_layer(workspace,
                               layer,
                               style_file=source_style_file_path)
    assert_style_file(workspace, layer, expected_style_file)
    with app.app_context():
        info = layer_util.get_layer_info(workspace, layer)
    assert info['style_type'] == expected_style_type

    process_client.delete_layer(workspace, layer)
