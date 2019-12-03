from celery import chain
import importlib
from multiprocessing import Process
import time
from celery.contrib.abortable import AbortableAsyncResult
import pytest

import sys
del sys.modules['layman']

from layman.layer import LAYER_TYPE
from layman import app as app, celery_app
from layman import settings
from layman import uuid
from layman.layer import util as layer_util
from layman.layer.filesystem import input_chunk
from layman import celery as celery_util


min_geojson = """
{
  "type": "Feature",
  "geometry": null,
  "properties": null
}
"""

num_layers_before_test = 0


@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    # print('before Process(target=app.run, kwargs={...')
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': settings.LAYMAN_SERVER_NAME.split(':')[1],
        'debug': False,
    })
    # print('before server.start()')
    server.start()
    time.sleep(1)

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    # print('before app.app_context()')
    with app.app_context() as ctx:
        publs_by_type = uuid.check_redis_consistency()
        global num_layers_before_test
        num_layers_before_test = len(publs_by_type[LAYER_TYPE])
        yield client

    # print('before server.terminate()')
    server.terminate()
    # print('before server.join()')
    server.join()


def test_single_abortable_task(client):
    task_names = [
        'layman.layer.filesystem.tasks.refresh_input_chunk',
    ]
    tasks = [
        getattr(
            importlib.import_module(taskname.rsplit('.', 1)[0]),
            taskname.rsplit('.', 1)[1]
        ) for taskname in task_names
    ]
    check_crs = False
    task_options = {
        'crs_id': 'EPSG:4326',
        'description': 'bla',
        'title': 'bla',
        'ensure_user': True,
        'check_crs': check_crs,
    }
    filenames = ['abc.geojson']
    username = 'test_abort_user'
    layername = 'test_abort_layer'
    files_to_upload = input_chunk.save_layer_files_str(username, layername, filenames, check_crs)
    task_chain = chain(*[
        layer_util._get_task_signature(username, layername, task_options, t)
        for t in tasks
    ])
    task_result = task_chain()

    results = [task_result]
    results_copy = [
        AbortableAsyncResult(task_result.task_id, backend=celery_app.backend)
        for task_result in results
    ]

    time.sleep(1)

    assert results[0].state == results_copy[0].state == 'STARTED'
    celery_util.abort_task_chain(results_copy)
    # first one is failure, because it throws AbortedException
    assert results[0].state == results_copy[0].state == 'FAILURE'
    layer_util.delete_layer(username, layername)


def test_abortable_task_chain(client):
    task_names = [
        'layman.layer.filesystem.tasks.refresh_input_chunk',
        'layman.layer.db.tasks.refresh_table',
        'layman.layer.geoserver.tasks.refresh_wfs',
    ]
    tasks = [
        getattr(
            importlib.import_module(taskname.rsplit('.', 1)[0]),
            taskname.rsplit('.', 1)[1]
        ) for taskname in task_names
    ]
    check_crs = False
    task_options = {
        'crs_id': 'EPSG:4326',
        'description': 'bla',
        'title': 'bla',
        'ensure_user': True,
        'check_crs': check_crs,
    }
    filenames = ['abc.geojson']
    username = 'test_abort_user'
    layername = 'test_abort_layer2'
    files_to_upload = input_chunk.save_layer_files_str(username, layername, filenames, check_crs)
    task_chain = chain(*[
        layer_util._get_task_signature(username, layername, task_options, t)
        for t in tasks
    ])
    task_result = task_chain()

    results = [task_result]
    prev_result = task_result
    while prev_result.parent is not None:
        prev_result = prev_result.parent
        results.insert(0, prev_result)
    assert len(results) == 3

    results_copy = [
        AbortableAsyncResult(task_result.task_id, backend=celery_app.backend)
        for task_result in results
    ]

    time.sleep(1)

    assert results[0].state == results_copy[0].state == 'STARTED'
    assert results[1].state == results_copy[1].state == 'PENDING'
    assert results[2].state == results_copy[2].state == 'PENDING'

    celery_util.abort_task_chain(results_copy)
    # first one is failure, because it throws AbortedException
    assert results[0].state == results_copy[0].state == 'FAILURE'
    # second one (and all others) was revoked, but it was not started at all because of previous failure, so it's pending for ever
    assert results[1].state == results_copy[1].state == 'ABORTED'
    assert results[2].state == results_copy[2].state == 'ABORTED'
    layer_util.delete_layer(username, layername)
