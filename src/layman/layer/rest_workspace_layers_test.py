import os
import sys
from urllib.parse import urljoin
from test import process_client, util as test_util
import requests
import pytest

del sys.modules['layman']

from layman import app, util as layman_util, settings
from layman.layer import util as layer_util
from layman.layer.filesystem import input_style
from layman.layer.geoserver.wms import DEFAULT_WMS_STORE_PREFIX
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
        process_client.publish_workspace_layer(username, name, title=title)

    # layers.GET
    with app.app_context():
        url = layman_util.url_for('rest_workspace_layers.get', workspace=username)
    rv = requests.get(url)
    assert rv.status_code == 200, rv.text

    for i in range(0, len(sorted_layers) - 1):
        assert rv.json()[i]["name"] == sorted_layers[i][0]
        assert rv.json()[i]["title"] == sorted_layers[i][1]

    for (name, title) in layers:
        process_client.delete_workspace_layer(username, name)


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
        info = layer_util.get_layer_info(workspace, layer)
    assert info['style_type'] == expected_style_type

    process_client.delete_workspace_layer(workspace, layer)
    process_client.publish_workspace_layer(workspace, layer)

    with app.app_context():
        info = layer_util.get_layer_info(workspace, layer)
    assert info['style_type'] == 'sld'
    assert info['style']['type'] == 'sld', info.get('style')
    assert info['style']['url'], info.get('style')

    assert_style_file(workspace, layer, None)

    process_client.patch_workspace_layer(workspace,
                                         layer,
                                         style_file=source_style_file_path)
    assert_style_file(workspace, layer, expected_style_file)
    with app.app_context():
        info = layer_util.get_layer_info(workspace, layer)
    assert info['style_type'] == expected_style_type

    process_client.delete_workspace_layer(workspace, layer)


class TestQgisCascadeWmsClass:
    workspace = 'test_qgis_cascade_wms_workspace'
    layer = 'test_qgis_cascade_wms_layer'
    qgis_layer_files = ['/code/tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson']
    qml_style_file = 'sample/style/ne_10m_admin_0_countries.qml'
    sld_layer_files = ['/code/tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson']
    sld_style_file = 'sample/style/generic-blue_sld.xml'
    expected_qgis_thumbnail = 'sample/style/test_qgis_style_applied_in_thumbnail_layer.png'
    expected_sld_thumbnail = 'sample/style/test_sld_style_applied_in_thumbnail_layer.png'

    @staticmethod
    def assert_wms_layer(workspace, layer, style, expected_thumbnail_path=None):
        expected_style_file = f'/layman_data_test/workspaces/{workspace}/layers/{layer}/input_style/{layer}'
        expected_qgis_file = f'/qgis/data/test/workspaces/{workspace}/layers/{layer}/{layer}.qgis'
        thumbnail_path = f'/layman_data_test/workspaces/{workspace}/layers/{layer}/thumbnail/{layer}.png'
        wms_stores_url = urljoin(settings.LAYMAN_GS_REST_WORKSPACES, f'{workspace}_wms/wmsstores/')
        wms_layers_url = urljoin(settings.LAYMAN_GS_REST_WORKSPACES, f'{workspace}_wms/wmslayers/')

        with app.app_context():
            info = layer_util.get_layer_info(workspace, layer)
        assert (info['style_type'] == 'qml') == (style == 'qml'), info.get('style_type', None)

        assert (os.path.exists(expected_style_file + '.qml')) == (style == 'qml')
        assert (os.path.exists(expected_style_file + '.sld')) == (style == 'sld')
        assert (os.path.exists(expected_qgis_file)) == (style == 'qml')
        assert info['style']['type'] == style if style else 'sld', info.get('style')
        assert info['style']['url'], info.get('style')

        rv = requests.get(wms_stores_url,
                          auth=settings.LAYMAN_GS_AUTH,
                          timeout=5,
                          )
        assert rv.status_code == 200, rv.json()
        if style == 'qml':
            assert rv.json()['wmsStores']['wmsStore'][0]['name'] == f'{DEFAULT_WMS_STORE_PREFIX}_{layer}', rv.json()

        rv = requests.get(wms_layers_url,
                          auth=settings.LAYMAN_GS_AUTH,
                          timeout=5,
                          )
        assert rv.status_code == 200, rv.json()
        if style == 'qgis':
            assert rv.json()['wmsLayers']['wmsLayer'][0]['name'] == layer, rv.json()

        if expected_thumbnail_path:
            diffs = test_util.compare_images(thumbnail_path, expected_thumbnail_path)
            assert diffs < 100

    @pytest.mark.flaky(reruns=2, reruns_delay=2)
    @pytest.mark.timeout(60)
    @pytest.mark.usefixtures('ensure_layman')
    @pytest.mark.parametrize('operations', [
        [
            ({'file_paths': qgis_layer_files, 'style_file': qml_style_file, }, 'qml', expected_qgis_thumbnail),
        ],
        [
            ({'file_paths': qgis_layer_files, }, None, None),
            ({'style_file': qml_style_file, }, 'qml', expected_qgis_thumbnail),
            ({'title': 'Title defined', }, 'qml', expected_qgis_thumbnail),
            ({'file_paths': sld_layer_files, }, 'qml', None),
            ({'style_file': sld_style_file, }, 'sld', expected_sld_thumbnail),
            ({'file_paths': qgis_layer_files, }, 'sld', None),
            ({'style_file': qml_style_file, }, 'qml', expected_qgis_thumbnail),
        ],
    ])
    def test_qgis_cascade_wms(self,
                              operations):
        workspace = self.workspace
        layer = self.layer

        for i, (params, expected_style, expected_thumbnail) in enumerate(operations):
            if i == 0:
                process_client.publish_workspace_layer(workspace,
                                                       layer,
                                                       **params)
            else:
                process_client.patch_workspace_layer(workspace,
                                                     layer,
                                                     **params)
            self.assert_wms_layer(workspace, layer, expected_style, expected_thumbnail)

        process_client.delete_workspace_layer(workspace, layer)
