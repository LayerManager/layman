import pytest
import lxml

from layman import LaymanError
from layman.layer.filesystem import input_style


@pytest.mark.parametrize('file_path, expected_type', [
    ('sample/style/generic-blue_sld.xml', 'sld'),
    ('sample/style/sld_1_1_0.xml', 'sld'),
    ('sample/style/funny_qml.xml', 'qgis'),
    ('sample/style/not_existing_file.xml', 'none'),
])
def test_get_style_type_from_xml_file(file_path,
                                      expected_type):
    detected_type = input_style.get_style_type_from_xml_file(file_path)
    assert detected_type.code == expected_type


@pytest.mark.parametrize('file_path, expected_error, expected_code', [
    ('sample/style/no_style.xml', LaymanError, 46),
    ('sample/style/countries_wms_blue.png', lxml.etree.XMLSyntaxError, 4),
])
def test_get_style_type_from_xml_file_errors(file_path,
                                             expected_error,
                                             expected_code):
    with pytest.raises(expected_error) as exc_info:
        _ = input_style.get_style_type_from_xml_file(file_path)
    assert exc_info.value.code == expected_code
