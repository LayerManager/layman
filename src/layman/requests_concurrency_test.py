import pytest

from layman import celery, common as common_const
from layman.common import empty_method_returns_true, redis
from layman.layer import LAYER_TYPE
from layman.layer.layer_class import Layer
from layman.map.map_class import Map
from test_tools import process_client


@pytest.mark.usefixtures('ensure_layman')
@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
def test_patch_after_feature_change_concurrency(publication_type):
    workspace = 'test_wfst_concurrency_workspace'
    publication_name = 'test_wfst_concurrency_layer'

    resp = process_client.publish_publication(publication_type, workspace, publication_name, )
    uuid = resp['uuid']
    publication = (
        Layer(uuid=uuid, layer_tuple=(workspace, publication_name), load=False)
        if publication_type == LAYER_TYPE
        else Map(uuid=uuid, map_tuple=(workspace, publication_name), load=False)
    )

    queue = celery.get_run_after_chain_queue(publication)
    assert not queue
    lock = redis.get_publication_lock(publication)
    assert not lock

    process_client.patch_after_feature_change(workspace, publication_type, publication_name)
    queue = celery.get_run_after_chain_queue(publication)
    assert len(queue) == 0, queue
    lock = redis.get_publication_lock(publication)
    assert lock == common_const.PUBLICATION_LOCK_FEATURE_CHANGE

    process_client.patch_publication(publication_type, uuid, title='New title',
                                     check_response_fn=empty_method_returns_true,
                                     raise_if_not_complete=False)
    queue = celery.get_run_after_chain_queue(publication)
    if publication_type == process_client.LAYER_TYPE:
        assert len(queue) == 1, queue
        assert queue == ['layman.util::patch_after_feature_change', ]
        lock = redis.get_publication_lock(publication)
        assert lock == common_const.PUBLICATION_LOCK_PATCH
        process_client.wait_for_publication_status(uuid, publication_type)

        process_client.patch_after_feature_change(workspace, publication_type, publication_name)
        queue = celery.get_run_after_chain_queue(publication)
    assert len(queue) == 0, queue
    lock = redis.get_publication_lock(publication)
    assert lock == common_const.PUBLICATION_LOCK_FEATURE_CHANGE

    process_client.patch_after_feature_change(workspace, publication_type, publication_name)
    queue = celery.get_run_after_chain_queue(publication)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]
    lock = redis.get_publication_lock(publication)
    assert lock == common_const.PUBLICATION_LOCK_FEATURE_CHANGE

    process_client.patch_after_feature_change(workspace, publication_type, publication_name)
    queue = celery.get_run_after_chain_queue(publication)
    assert len(queue) == 1, queue
    assert queue == ['layman.util::patch_after_feature_change', ]
    lock = redis.get_publication_lock(publication)
    assert lock == common_const.PUBLICATION_LOCK_FEATURE_CHANGE

    process_client.wait_for_publication_status(uuid, publication_type)
    queue = celery.get_run_after_chain_queue(publication)
    assert not queue, queue
    lock = redis.get_publication_lock(publication)
    assert not lock

    process_client.delete_publication(publication_type, uuid=uuid)

    queue = celery.get_run_after_chain_queue(publication)
    assert not queue, queue
    lock = redis.get_publication_lock(publication)
    assert not lock
