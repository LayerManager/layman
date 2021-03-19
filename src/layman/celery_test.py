from celery import chain
import importlib
import time
from celery.contrib.abortable import AbortableAsyncResult

import sys

del sys.modules['layman']

from layman import app as app, celery_app
from layman.layer.filesystem import input_chunk
from layman import celery as celery_util
from layman.common import tasks as tasks_util
from test import flask_client

min_geojson = """
{
  "type": "Feature",
  "geometry": null,
  "properties": null
}
"""

num_layers_before_test = 0

client = flask_client.client


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
    with app.app_context():
        input_chunk.save_layer_files_str(username, layername, filenames, check_crs)
    task_chain = chain(*[
        tasks_util._get_task_signature(username, layername, t, task_options, 'layername')
        for t in tasks
    ])
    task_result = task_chain()

    results = [task_result]
    results_copy = [
        AbortableAsyncResult(task_result.task_id, backend=celery_app.backend)
        for task_result in results
    ]

    i = 1
    while i <= 20 and not (results[0].state == results_copy[0].state == 'STARTED'):
        print(f"results[0].state={results[0].state}, results_copy[0].state={results_copy[0].state}")
        time.sleep(0.1)
        i += 1

    assert results[0].state == results_copy[0].state == 'STARTED'
    with app.app_context():
        celery_util.abort_task_chain(results_copy)
    # first one is failure, because it throws AbortedException
    assert results[0].state == results_copy[0].state == 'FAILURE'
    with app.app_context():
        input_chunk.delete_layer(username, layername)


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
    with app.app_context():
        input_chunk.save_layer_files_str(username, layername, filenames, check_crs)
    task_chain = chain(*[
        tasks_util._get_task_signature(username, layername, t, task_options, 'layername')
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

    with app.app_context():
        celery_util.abort_task_chain(results_copy)
    # first one is failure, because it throws AbortedException
    assert results[0].state == results_copy[0].state == 'FAILURE'
    # second one (and all others) was revoked, but it was not started at all because of previous failure, so it's pending for ever
    assert results[1].state == results_copy[1].state == 'ABORTED'
    assert results[2].state == results_copy[2].state == 'ABORTED'
    with app.app_context():
        input_chunk.delete_layer(username, layername)
