import lxml
import pytest
from werkzeug.datastructures import FileStorage

from layman import LaymanError
from layman.layer.filesystem import input_style


@pytest.mark.parametrize('file_path, expected_type', [
    ('sample/style/generic-blue_sld.xml', 'sld'),
    ('sample/style/sld_1_1_0.xml', 'sld'),
    ('sample/style/small_layer.qml', 'qml'),
    (None, 'sld'),
])
def test_get_style_type_from_xml_file(file_path,
                                      expected_type):
    if file_path:
        with open(file_path, 'rb') as file:
            file = FileStorage(file)
            detected_type = input_style.get_style_type_from_file_storage(file)
    else:
        detected_type = input_style.get_style_type_from_file_storage(file_path)
    assert detected_type.code == expected_type


@pytest.mark.parametrize('file_path, expected_error, expected_code', [
    ('sample/style/no_style.xml', LaymanError, 46),
    ('sample/style/countries_wms_blue.png', lxml.etree.XMLSyntaxError, 4),
])
def test_get_style_type_from_xml_file_errors(file_path,
                                             expected_error,
                                             expected_code):
    with pytest.raises(expected_error) as exc_info:
        with open(file_path, 'rb') as file:
            file = FileStorage(file)
            input_style.get_style_type_from_file_storage(file)
    assert exc_info.value.code == expected_code


@pytest.mark.parametrize('filepath, exp_set', [
    ('test_tools/data/style/small_layer_external_circle.qml', {'/home/work/PycharmProjects/layman/test_tools/data/style/circle.svg', }),
])
def test_get_external_files_from_qml_file(filepath, exp_set):
    found_files = input_style.get_external_files_from_qml_file(filepath)
    assert found_files == exp_set
