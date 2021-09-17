import pytest

from test_tools import process_client


@pytest.mark.parametrize('style_file, expected_json', [
    ('test_tools/data/style/small_layer_external_circle.qml', {'type': 'qml',
                                                               'external_files': ['./circle-15.svg', ]})
])
@pytest.mark.usefixtures('ensure_layman')
def test_get_style_info(style_file, expected_json):
    style_info = process_client.get_style_info(style_file=style_file)
    assert style_info == expected_json
