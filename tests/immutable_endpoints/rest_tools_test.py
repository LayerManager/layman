import pytest

from layman import LaymanError
from test_tools import process_client, util as test_util


@pytest.mark.parametrize('style_file, expected_json', [
    ('test_tools/data/style/small_layer_external_circle.qml', {'type': 'qml',
                                                               'external_files': {'/home/work/PycharmProjects/layman/test_tools/data/style/circle.svg', }}),
    ('test_tools/data/style/sample_point_layer_external_circle.qml', {'type': 'qml',
                                                                      'external_files': {
                                                                          '/home/work/PycharmProjects/layman/test_tools/data/style/circle.svg', }}),
    ('sample/style/generic-blue_sld.xml', {'type': 'sld', }),
])
@pytest.mark.usefixtures('ensure_layman')
def test_post_style_info(style_file, expected_json):
    style_info = process_client.post_style_info(style_file=style_file)
    if 'external_files' in style_info:
        style_info['external_files'] = set(style_info['external_files'])
    assert style_info == expected_json


@pytest.mark.parametrize('params, expected_exc', [
    (dict(),
     {'http_code': 400,
      'code': 1,
      'message': 'Missing parameter',
      'detail': {'parameter': 'style', },
      },
     ),
    ({'style_file': 'test_tools/data/thumbnail/layer_square_external_svg.png'},
     {'http_code': 400,
      'code': 46,
      'message': 'Unknown style file. Can recognize only SLD and QML files.',
      },
     ),
])
@pytest.mark.usefixtures('ensure_layman')
def test_post_style_info_error(params, expected_exc):
    with pytest.raises(LaymanError) as exc_info:
        process_client.post_style_info(**params)
    test_util.assert_error(expected_exc, exc_info)
