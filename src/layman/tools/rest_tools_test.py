import pytest

from layman import LaymanError
from test_tools import process_client, util as test_util


@pytest.mark.parametrize('style_file, expected_json', [
    ('test_tools/data/style/small_layer_external_circle.qml', {'type': 'qml',
                                                               'external_files': ['./circle-15.svg', ]})
])
@pytest.mark.usefixtures('ensure_layman')
def test_get_style_info(style_file, expected_json):
    style_info = process_client.get_style_info(style_file=style_file)
    assert style_info == expected_json


@pytest.mark.parametrize('params, expected_exc', [
    ({'style_file': 'sample/style/generic-blue_sld.xml',
      },
     {'http_code': 400,
      'code': 2,
      'message': 'Wrong parameter value',
      'detail': {'parameter': 'style', 'supported_values': ['qml']},
      },
     ),
    (dict(),
     {'http_code': 400,
      'code': 1,
      'message': 'Missing parameter',
      'detail': {'parameter': 'style', },
      },
     ),
])
@pytest.mark.usefixtures('ensure_layman')
def test_get_style_info_error(params, expected_exc):
    with pytest.raises(LaymanError) as exc_info:
        process_client.get_style_info(**params)
    test_util.assert_error(expected_exc, exc_info)
