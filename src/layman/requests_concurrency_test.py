import pytest

from layman import celery, common as common_const
from layman.common import empty_method_returns_true, redis
from test_tools import process_client


@pytest.mark.usefixtures('ensure_layman')
@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
def test_patch_after_feature_change_concurrency(publication_type):
    workspace = 'test_wfst_concurrency_workspace'
    publication = 'test_wfst_concurrency_layer'

    process_client.publish_workspace_publication(publication_type, workspace, publication, )

    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert not queue
    lock = redis.get_publication_lock(workspace, publication_type, publication)
    assert not lock

    process_client.patch_after_feature_change(workspace, publication_type, publication)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert len(queue) == 0, queue
    lock = redis.get_publication_lock(workspace, publication_type, publication)
    assert lock == common_const.PUBLICATION_LOCK_FEATURE_CHANGE

    process_client.patch_workspace_publication(publication_type, workspace, publication, title='New title',
                                               check_response_fn=empty_method_returns_true,
                                               raise_if_not_complete=False)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert len(queue) == 0, queue
    lock = redis.get_publication_lock(workspace, publication_type, publication)
    assert lock == common_const.PUBLICATION_LOCK_FEATURE_CHANGE

    process_client.patch_after_feature_change(workspace, publication_type, publication)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]
    lock = redis.get_publication_lock(workspace, publication_type, publication)
    assert lock == common_const.PUBLICATION_LOCK_FEATURE_CHANGE

    process_client.patch_after_feature_change(workspace, publication_type, publication)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]
    lock = redis.get_publication_lock(workspace, publication_type, publication)
    assert lock == common_const.PUBLICATION_LOCK_FEATURE_CHANGE

    process_client.wait_for_publication_status(workspace, publication_type, publication)
    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert not queue, queue
    lock = redis.get_publication_lock(workspace, publication_type, publication)
    assert not lock

    process_client.delete_workspace_publication(publication_type, workspace, publication, )

    queue = celery.get_run_after_chain_queue(workspace, publication_type, publication)
    assert not queue, queue
    lock = redis.get_publication_lock(workspace, publication_type, publication)
    assert not lock
