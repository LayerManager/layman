import math
import os
import pytest
from layman import app, settings
from layman.layer.qgis import wms
from layman.layer.filesystem import gdal, input_file
from layman.util import get_publication_uuid
from test_tools.util import url_for
from ...asserts.final.publication import internal as asserts_internal
from ... import static_data as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_RASTER_LAYERS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_raster_files(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    with app.app_context():
        layer_uuid = get_publication_uuid(workspace, publ_type, publication)
        directory_path = input_file.get_layer_input_file_dir(layer_uuid)
    publ_test_data = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]
    for ext in publ_test_data['file_extensions']:
        file_path = os.path.join(directory_path, layer_uuid + ext)
        assert os.path.exists(file_path), file_path
    norm_file_path = gdal.get_normalized_raster_layer_main_filepaths(layer_uuid)[0]
    assert os.path.exists(norm_file_path), norm_file_path
    normalized_color_interp = publ_test_data['normalized_color_interp']
    assert normalized_color_interp == gdal.get_color_interpretations(norm_file_path)

    # check number of overviews
    raster_size = max(gdal.get_raster_size(norm_file_path))
    overview_counts = gdal.get_overview_counts(norm_file_path)
    # https://gdal.org/en/stable/programs/gdaladdo.html#cmdoption-gdaladdo-minsize
    exp_overview_count = max(math.ceil(math.log(raster_size / 256, 2)), 0)
    assert overview_counts == [exp_overview_count] * len(overview_counts)
    exp_def_overview_count = publ_test_data.get('normalized_overviews')
    if exp_def_overview_count is not None:
        assert overview_counts == [exp_def_overview_count] * len(overview_counts)

    asserts_internal.nodata_preserved_in_normalized_raster(workspace, publ_type, publication)
    asserts_internal.size_and_position_preserved_in_normalized_raster(workspace, publ_type, publication)
    asserts_internal.stats_preserved_in_normalized_raster(workspace, publ_type, publication)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_QML_LAYERS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_qml_files(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    with app.app_context():
        publ_uuid = get_publication_uuid(workspace, publ_type, publication)
    layer_directory = f'{settings.LAYMAN_QGIS_DATA_DIR}/layers/{publ_uuid}'

    assert os.path.exists(layer_directory)
    with app.app_context():
        url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=publication, internal=False)
        assert wms.get_layer_info(workspace, publication) == {'name': publication,
                                                              'style': {'type': 'qml',
                                                                        'url': url},
                                                              '_wms': {
                                                                  'qgis_capabilities_url': f'{settings.LAYMAN_QGIS_URL}?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.1.1&'
                                                                                           f'map=/qgis/data/test/layers/{publ_uuid}/{publ_uuid}.qgis'
                                                              }
                                                              }
