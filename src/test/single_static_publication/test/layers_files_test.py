import os
import pytest
from layman import app
from layman.layer.filesystem import gdal, input_file
from ... import single_static_publication as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_RASTER_LAYERS)
@pytest.mark.usefixtures('ensure_layman')
def test_files(workspace, publ_type, publication):
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
