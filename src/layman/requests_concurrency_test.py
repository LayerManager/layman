from test import process_client
import pytest

from layman import celery, util as layman_util, app
from layman.common import empty_method_returns_true


@pytest.mark.usefixtures('ensure_layman')
@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
def test_patch_after_feature_change_concurrency(publication_type):
    workspace = 'test_wfst_concurrency_workspace'
    publication = 'test_wfst_concurrency_layer'

    process_client.publish_workspace_publication(publication_type, workspace, publication, )

    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert not queue

    with app.app_context():
        layman_util.patch_after_feature_change(workspace, publication_type, publication)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert len(queue) == 0, queue

    process_client.patch_workspace_publication(publication_type, workspace, publication, title='New title',
                                               check_response_fn=empty_method_returns_true)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]

    with app.app_context():
        layman_util.patch_after_feature_change(workspace, publication_type, publication)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]

    with app.app_context():
        layman_util.patch_after_feature_change(workspace, publication_type, publication)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]

    process_client.wait_for_publication_status(workspace, publication_type, publication)

    process_client.delete_workspace_publication(publication_type, workspace, publication, )

    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert not queue, queue
