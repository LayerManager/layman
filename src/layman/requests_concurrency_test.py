from test import process_client
import pytest

from layman import celery, util as layman_util, app
from layman.common import empty_method_returns_true


@pytest.mark.usefixtures('ensure_layman')
def test_patch_after_feature_change_concurrency():
    workspace = 'test_wfst_concurrency_workspace'
    layer = 'test_wfst_concurrency_layer'
    publication_type = process_client.LAYER_TYPE

    process_client.publish_workspace_publication(publication_type, workspace, layer, )

    queue = celery.get_run_after_chain_queue(workspace, publication_type, layer)
    assert not queue

    with app.app_context():
        layman_util.patch_after_feature_change(workspace, publication_type, layer)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, layer)
    assert len(queue) == 0, queue

    process_client.patch_workspace_publication(publication_type, workspace, layer, title='New title',
                                               check_response_fn=empty_method_returns_true)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, layer)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]

    with app.app_context():
        layman_util.patch_after_feature_change(workspace, publication_type, layer)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, layer)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]

    with app.app_context():
        layman_util.patch_after_feature_change(workspace, publication_type, layer)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, layer)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]

    process_client.wait_for_publication_status(workspace, publication_type, layer)

    process_client.delete_workspace_publication(publication_type, workspace, layer, )

    queue = celery.get_run_after_chain_queue(workspace, publication_type, layer)
    assert not queue, queue
