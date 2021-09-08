import pytest

from layman import LaymanError, settings
from test_tools import process_client, util as test_util

COMMON_WORKSPACE = 'failed_publications_workspace'


@pytest.mark.usefixtures('ensure_layman')
def test_png_without_crs():
    workspace = COMMON_WORKSPACE
    layer = 'test_png_without_crs_layer'

    expected_exc = {'http_code': 400,
                    'code': 4,
                    'message': 'Unsupported CRS of data file',
                    'detail': {'found': 'None', 'supported_values': settings.INPUT_SRS_LIST},
                    }

    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_layer(workspace, layer,
                                               file_paths=['sample/layman.layer/sample_png_pgw_rgba.pgw',
                                                           'sample/layman.layer/sample_png_pgw_rgba.png', ], )
    test_util.assert_error(expected_exc, exc_info)
