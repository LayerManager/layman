import json
import sys
import requests
import pytest

del sys.modules['layman']
from layman import app, LaymanError
from test_tools import process_client, util as test_util
from test_tools.util import url_for


@pytest.mark.usefixtures('ensure_layman')
def test_style_value():
    username = 'test_style_value_user'
    layername = 'test_style_value_layer'

    process_client.publish_workspace_layer(username, layername)

    with app.app_context():
        layer_url = url_for('rest_workspace_layer.get', workspace=username, layername=layername)
        expected_style_url = url_for('rest_workspace_layer_style.get', workspace=username, layername=layername,
                                     internal=False)
    response = requests.get(layer_url)
    assert response.status_code == 200, response.text
    resp_json = json.loads(response.text)

    assert 'style' in resp_json, response.text
    assert 'url' in resp_json['style'], response.text
    assert 'status' not in resp_json['style'], response.text

    external_style_url = resp_json['style']['url']
    assert external_style_url == expected_style_url, (response.text, external_style_url)

    with app.app_context():
        style_url = url_for('rest_workspace_layer_style.get', workspace=username, layername=layername)

    r_get = requests.get(style_url)
    assert r_get.status_code == 200, (r_get.text, style_url)

    r_del = requests.delete(style_url)
    assert r_del.status_code >= 400, (r_del.text, style_url)

    process_client.delete_workspace_layer(username, layername)


@pytest.mark.parametrize('post_params, patch_params, expected_exc', [
    ({'file_paths': ['sample/layman.layer/sample_tif_rgb.tif', ],
      },
     {'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
      },
     {'http_code': 400,
      'code': 48,
      'message': 'Wrong combination of parameters',
      'detail': 'Raster layers are not allowed to have QML style.',
      },
     ),
    ({'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
      },
     {'file_paths': ['sample/layman.layer/sample_tif_rgb.tif', ],
      },
     {'http_code': 400,
      'code': 48,
      'message': 'Wrong combination of parameters',
      'detail': 'Raster layers are not allowed to have QML style.',
      },
     ),
])
@pytest.mark.usefixtures('ensure_layman')
def test_error(post_params, patch_params, expected_exc):
    workspace = 'test_error_workspace'
    layer = 'test_error_layer'

    process_client.publish_workspace_layer(workspace, layer, **post_params)
    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_layer(workspace, layer, **patch_params)
    test_util.assert_error(expected_exc, exc_info)
    process_client.delete_workspace_layer(workspace, layer)
