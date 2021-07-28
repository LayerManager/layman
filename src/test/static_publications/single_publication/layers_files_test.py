import os
import pytest
from layman import app, settings
from layman.layer import qgis
from layman.layer.qgis import wms
from layman.layer.filesystem import gdal, input_file
from test_tools import process_client
from test_tools.util import url_for
from ... import static_publications as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_RASTER_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_raster_files(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    with app.app_context():
        directory_path = input_file.get_layer_input_file_dir(workspace, publication)
    for ext in data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['file_extensions']:
        file_path = os.path.join(directory_path, publication + ext)
        assert os.path.exists(file_path), file_path
    norm_file_path = gdal.get_normalized_raster_layer_main_filepath(workspace, publication)
    assert os.path.exists(norm_file_path), norm_file_path
    normalized_color_interp = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['normalized_color_interp']
    assert normalized_color_interp == gdal.get_color_interpretations(norm_file_path)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_QML_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_qml_files(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    workspace_directory = f'{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}'
    layer_directory = f'{workspace_directory}/layers/{publication}'

    assert os.path.exists(workspace_directory)
    assert os.path.exists(layer_directory)
    with app.app_context():
        url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=publication, internal=False)
        assert wms.get_layer_info(workspace, publication) == {'name': publication,
                                                              'style': {'type': 'qml',
                                                                        'url': url},
                                                              '_wms': {
                                                                  'qgis_capabilities_url': f'{settings.LAYMAN_QGIS_URL}?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.1.1&'
                                                                                           f'map=/qgis/data/test/workspaces/{workspace}/layers/{publication}/{publication}.qgis'
                                                              }
                                                              }
        assert workspace in qgis.get_workspaces()

    process_client.delete_workspace_layer(workspace, publication)
    assert os.path.exists(workspace_directory)
    assert not os.path.exists(layer_directory)
    with app.app_context():
        assert wms.get_layer_info(workspace, publication) == {}
        assert workspace in qgis.get_workspaces()
