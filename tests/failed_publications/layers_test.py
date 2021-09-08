import pytest

from layman import LaymanError, settings
from test_tools import process_client, util as test_util

LAYER_TYPE = process_client.LAYER_TYPE
COMMON_WORKSPACE = 'failed_publications_workspace'
LAYER = 'test_png_without_crs_layer'


@pytest.mark.parametrize('params, expected_exc, error_async_part', [
    (
            {'file_paths': ['sample/layman.layer/sample_png_pgw_rgba.pgw',
                            'sample/layman.layer/sample_png_pgw_rgba.png', ]},
            {'http_code': 400,
             'code': 4,
             'message': 'Unsupported CRS of data file',
             'detail': {'found': 'None', 'supported_values': settings.INPUT_SRS_LIST},
             },
            'file',
    ),
])
@pytest.mark.usefixtures('ensure_layman')
def test_publication_error(params, expected_exc, error_async_part):
    publ_type = LAYER_TYPE
    workspace = COMMON_WORKSPACE
    layer = LAYER

    # Synchronous POST
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_publication(publ_type, workspace, layer,
                                                     **params, )
    test_util.assert_error(expected_exc, exc_info)

    # Asynchronous POST
    process_client.publish_workspace_publication(publ_type, workspace, layer,
                                                 **params,
                                                 with_chunks=True,
                                                 )
    info = process_client.get_workspace_publication(publ_type, workspace, layer, )
    test_util.assert_async_error(expected_exc, info[error_async_part]['error'])

    # Preparation for PATCH tests
    process_client.delete_workspace_layer(workspace, layer)
    process_client.publish_workspace_publication(publ_type, workspace, layer,)

    # Synchronous PATCH
    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_publication(publ_type, workspace, layer,
                                                   **params, )
    test_util.assert_error(expected_exc, exc_info)

    # Preparation for PATCH tests
    process_client.delete_workspace_layer(workspace, layer)
    process_client.publish_workspace_publication(publ_type, workspace, layer,)

    # Asynchronous PATCH
    process_client.patch_workspace_publication(publ_type, workspace, layer,
                                               **params,
                                               with_chunks=True,
                                               )
    info = process_client.get_workspace_publication(publ_type, workspace, layer, )
    test_util.assert_async_error(expected_exc, info[error_async_part]['error'])

    process_client.delete_workspace_layer(workspace, layer)
