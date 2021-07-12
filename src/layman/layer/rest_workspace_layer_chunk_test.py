import pytest

from test_tools import process_client


@pytest.mark.parametrize('file_path', [
    'sample/layman.layer/small_layer.geojson',
    'sample/layman.layer/sample_tif_rgb.tif',
])
@pytest.mark.usefixtures('ensure_layman')
def test_post_vector_chunk_layer(file_path):
    workspace = 'test_post_vector_chunk_layer_workspace'
    layer = 'test_post_vector_chunk_layer_layer'

    process_client.publish_workspace_layer(workspace,
                                           layer,
                                           file_paths=[file_path],
                                           with_chunks=True)

    process_client.delete_workspace_layer(workspace, layer)
