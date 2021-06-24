import os
import sys
from urllib.parse import urljoin
from test import process_client, util as test_util, assert_util
from test.util import url_for
import requests
import pytest

del sys.modules['layman']

from geoserver import GS_REST_WORKSPACES
from layman import app, settings, util as layman_util, LaymanError
from layman.layer import util as layer_util
from layman.layer.filesystem import input_style, input_file, gdal, thumbnail as fs_thumbnail
from layman.layer.geoserver.wms import DEFAULT_WMS_QGIS_STORE_PREFIX
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
        url = url_for('rest_workspace_layers.get', workspace=username)
    response = requests.get(url)
    assert response.status_code == 200, response.text

    for i in range(0, len(sorted_layers) - 1):
        assert response.json()[i]["name"] == sorted_layers[i][0]
        assert response.json()[i]["title"] == sorted_layers[i][1]

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
        info = layer_util.get_layer_info(workspace, layer, context={'keys': ['style_type', 'style'], })
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
        wms_stores_url = urljoin(GS_REST_WORKSPACES, f'{workspace}_wms/wmsstores/')
        wms_layers_url = urljoin(GS_REST_WORKSPACES, f'{workspace}_wms/wmslayers/')

        with app.app_context():
            info = layer_util.get_layer_info(workspace, layer, context={'keys': ['style_type', 'style'], })
        assert (info['style_type'] == 'qml') == (style == 'qml'), info.get('style_type', None)

        assert (os.path.exists(expected_style_file + '.qml')) == (style == 'qml')
        assert (os.path.exists(expected_style_file + '.sld')) == (style == 'sld')
        assert (os.path.exists(expected_qgis_file)) == (style == 'qml')
        assert info['style']['type'] == style if style else 'sld', info.get('style')
        assert info['style']['url'], info.get('style')

        response = requests.get(wms_stores_url,
                                auth=settings.LAYMAN_GS_AUTH,
                                timeout=5,
                                )
        assert response.status_code == 200, response.json()
        if style == 'qml':
            assert response.json()['wmsStores']['wmsStore'][0]['name'] == f'{DEFAULT_WMS_QGIS_STORE_PREFIX}_{layer}', response.json()

        response = requests.get(wms_layers_url,
                                auth=settings.LAYMAN_GS_AUTH,
                                timeout=5,
                                )
        assert response.status_code == 200, response.json()
        if style == 'qgis':
            assert response.json()['wmsLayers']['wmsLayer'][0]['name'] == layer, response.json()

        if expected_thumbnail_path:
            diffs = test_util.compare_images(thumbnail_path, expected_thumbnail_path)
            assert diffs < 100

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


def assert_raster_layer(workspace, layer, file_names, exp_bbox, exp_thumbnail):
    with app.app_context():
        info = layman_util.get_publication_info(workspace, process_client.LAYER_TYPE, layer, context={'keys': ['file', 'bounding_box', 'wms']})
        directory_path = input_file.get_layer_input_file_dir(workspace, layer)
    assert info.get('file', dict()).get('file_type') == 'raster', info
    for file in file_names:
        file_path = os.path.join(directory_path, layer + os.path.splitext(file)[1])
        assert os.path.exists(file_path), file_path
    norm_file_path = gdal.get_normalized_raster_layer_main_filepath(workspace, layer)
    assert os.path.exists(norm_file_path), norm_file_path

    bbox = gdal.get_bbox(workspace, layer)
    assert_util.assert_same_bboxes(bbox, exp_bbox, 0.01)
    info_bbox = info['bounding_box']
    assert_util.assert_same_bboxes(info_bbox, exp_bbox, 0.01)

    assert 'wms' in info, info
    assert 'url' in info['wms'], info

    with app.app_context():
        thumbnail_path = fs_thumbnail.get_layer_thumbnail_path(workspace, layer)
    diffs = test_util.compare_images(exp_thumbnail, thumbnail_path)
    assert diffs < 1000


@pytest.mark.parametrize('layer_suffix, file_paths, bbox, thumbnail', [
    ('jp2', ['sample/layman.layer/sample_jp2_rgb.jp2', ], (1829708, 6308828.600, 1833166.200, 6310848.600), '/code/test/data/thumbnail/raster_layer_jp2.png', ),
    ('tif', ['sample/layman.layer/sample_tif_rgb.tif', ], (1679391.080, 6562360.440, 1679416.230, 6562381.790), '/code/test/data/thumbnail/raster_layer_tif.png', ),
    ('tiff', ['sample/layman.layer/sample_tiff_rgba.tiff', ], (1669480, 6580973, 1675352, 6586999,), '/code/test/data/thumbnail/raster_layer_tiff.png', ),
    ('tif_tfw', ['sample/layman.layer/sample_tif_tfw_rgba.tif', 'sample/layman.layer/sample_tif_tfw_rgba.tfw'],
     (1669480, 6580973, 1675352, 6586999,), '/code/test/data/thumbnail/raster_layer_tiff.png', ),
])
@pytest.mark.usefixtures('ensure_layman')
def test_post_raster(layer_suffix, file_paths, bbox, thumbnail, ):
    workspace = 'test_post_raster_workspace'
    layer_prefix = 'test_post_raster'
    layer = layer_prefix + '_' + layer_suffix

    process_client.publish_workspace_layer(workspace, layer, file_paths=file_paths)
    assert_raster_layer(workspace, layer, file_paths, bbox, thumbnail, )
    process_client.delete_workspace_layer(workspace, layer)

    process_client.publish_workspace_layer(workspace, layer)
    process_client.patch_workspace_layer(workspace, layer, file_paths=file_paths)
    assert_raster_layer(workspace, layer, file_paths, bbox, thumbnail, )
    process_client.delete_workspace_layer(workspace, layer)


@pytest.mark.parametrize('post_params, expected_exc', [
    ({'file_paths': ['sample/layman.layer/sample_tif_rgb.tif', ],
      'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
      },
     {'http_code': 400,
      'code': 48,
      'message': 'Wrong combination of parameters',
      'detail': 'Raster layers are not allowed to have QML style.',
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
