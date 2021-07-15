import sys
import pytest

del sys.modules['layman']
from layman import LaymanError
from test_tools import process_client, util as test_util


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
