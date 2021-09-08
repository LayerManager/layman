import pytest

from layman import LaymanError
from test_tools import process_client, util as test_util
from .. import failed_publications

LAYER_TYPE = process_client.LAYER_TYPE
COMMON_WORKSPACE = 'failed_publications_workspace'
LAYER = 'test_png_without_crs_layer'


@pytest.mark.parametrize('layer_def', failed_publications.LAYER_DEFINITIONS)
@pytest.mark.usefixtures('ensure_layman')
def test_publication_error_post(layer_def):
    publ_type = LAYER_TYPE
    workspace = COMMON_WORKSPACE
    layer = LAYER

    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_publication(publ_type, workspace, layer,
                                                     **layer_def[failed_publications.DEFINITION], )
    test_util.assert_error(layer_def[failed_publications.TEST_DATA]['expected_exc'], exc_info)


@pytest.mark.parametrize('layer_def', failed_publications.LAYER_CHUNK_ASYNC_ERROR_DEFINITIONS)
@pytest.mark.usefixtures('ensure_layman')
def test_publication_error_chunk_post_async_error(layer_def):
    publ_type = LAYER_TYPE
    workspace = COMMON_WORKSPACE
    layer = LAYER

    process_client.publish_workspace_publication(publ_type, workspace, layer,
                                                 **layer_def[failed_publications.DEFINITION],
                                                 with_chunks=True,
                                                 )
    info = process_client.get_workspace_publication(publ_type, workspace, layer, )
    test_util.assert_async_error(layer_def[failed_publications.TEST_DATA]['expected_exc'],
                                 info[layer_def[failed_publications.TEST_DATA]['error_async_part']]['error'])

    process_client.delete_workspace_layer(workspace, layer)


@pytest.mark.parametrize('layer_def', failed_publications.LAYER_CHUNK_SYNC_ERROR_DEFINITIONS)
@pytest.mark.usefixtures('ensure_layman')
def test_publication_error_chunk_post(layer_def):
    publ_type = LAYER_TYPE
    workspace = COMMON_WORKSPACE
    layer = LAYER

    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_publication(publ_type, workspace, layer,
                                                     **layer_def[failed_publications.DEFINITION],
                                                     with_chunks=True,
                                                     )
    test_util.assert_error(layer_def[failed_publications.TEST_DATA]['expected_exc'], exc_info)


@pytest.mark.parametrize('layer_def', failed_publications.LAYER_DEFINITIONS)
@pytest.mark.usefixtures('ensure_layman')
def test_publication_error_patch(layer_def):
    publ_type = LAYER_TYPE
    workspace = COMMON_WORKSPACE
    layer = LAYER

    process_client.publish_workspace_publication(publ_type, workspace, layer,)

    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_publication(publ_type, workspace, layer,
                                                   **layer_def[failed_publications.DEFINITION], )
    test_util.assert_error(layer_def[failed_publications.TEST_DATA]['expected_exc'], exc_info)

    process_client.delete_workspace_layer(workspace, layer)


@pytest.mark.parametrize('layer_def', failed_publications.LAYER_CHUNK_ASYNC_ERROR_DEFINITIONS)
@pytest.mark.usefixtures('ensure_layman')
def test_publication_error_chunk_patch_async_error(layer_def):
    publ_type = LAYER_TYPE
    workspace = COMMON_WORKSPACE
    layer = LAYER

    process_client.publish_workspace_publication(publ_type, workspace, layer,)

    process_client.patch_workspace_publication(publ_type, workspace, layer,
                                               **layer_def[failed_publications.DEFINITION],
                                               with_chunks=True,
                                               )
    info = process_client.get_workspace_publication(publ_type, workspace, layer, )
    test_util.assert_async_error(layer_def[failed_publications.TEST_DATA]['expected_exc'],
                                 info[layer_def[failed_publications.TEST_DATA]['error_async_part']]['error'])

    process_client.delete_workspace_layer(workspace, layer)


@pytest.mark.parametrize('layer_def', failed_publications.LAYER_CHUNK_SYNC_ERROR_DEFINITIONS)
@pytest.mark.usefixtures('ensure_layman')
def test_publication_error_chunk_patch(layer_def):
    publ_type = LAYER_TYPE
    workspace = COMMON_WORKSPACE
    layer = LAYER

    process_client.publish_workspace_publication(publ_type, workspace, layer,)

    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_publication(publ_type, workspace, layer,
                                                   **layer_def[failed_publications.DEFINITION],
                                                   with_chunks=True,
                                                   )
    test_util.assert_error(layer_def[failed_publications.TEST_DATA]['expected_exc'], exc_info)

    process_client.delete_workspace_layer(workspace, layer)
