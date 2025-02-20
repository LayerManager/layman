import importlib
import time
import sys
import pytest
from celery import chain
from celery.contrib.abortable import AbortableAsyncResult

del sys.modules['layman']

from layman import app, celery_app
from layman.layer.filesystem import input_chunk, util as fs_util
from layman import celery as celery_util
from layman.common import tasks as tasks_util
from test_tools import flask_client

MIN_GEOJSON = """
{
  "type": "Feature",
  "geometry": null,
  "properties": null
}
"""

NUM_LAYERS_BEFORE_TEST = 0

client = flask_client.client


@pytest.mark.usefixtures('client')
def test_single_abortable_task():
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
    publ_uuid = '956fc92b-4247-4ea9-a014-59d8b09acd0a'
    task_options = {
        'crs_id': 'EPSG:4326',
        'description': 'bla',
        'title': 'bla',
        'check_crs': check_crs,
        'uuid': publ_uuid,
    }
    filenames = fs_util.InputFiles(sent_paths=['abc.geojson'])
    workspace = 'test_abort_workspace'
    layername = 'test_abort_layer'
    with app.app_context():
        input_chunk.save_layer_files_str(publ_uuid, filenames, check_crs)
    task_chain = chain(*[
        tasks_util.get_task_signature(workspace, layername, t, task_options, 'layername')
        for t in tasks
    ])
    task_result = task_chain()

    results = [task_result]
    results_copy = [
        AbortableAsyncResult(task_result.task_id, backend=celery_app.backend)
        for task_result in results
    ]

    i = 1
    while i <= 20 and not results[0].state == results_copy[0].state == 'STARTED':
        print(f"results[0].state={results[0].state}, results_copy[0].state={results_copy[0].state}")
        time.sleep(0.1)
        i += 1

    assert results[0].state == results_copy[0].state == 'STARTED'
    with app.app_context():
        celery_util.abort_task_chain(results_copy)
    # first one is failure, because it throws AbortedException
    assert results[0].state == results_copy[0].state == 'FAILURE'
    with app.app_context():
        input_chunk.delete_layer_by_uuid(publ_uuid)


@pytest.mark.usefixtures('client')
def test_abortable_task_chain():
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
    publ_uuid = '6658cfe1-4090-4f0a-949b-a0891bec2ef4'
    task_options = {
        'crs_id': 'EPSG:4326',
        'description': 'bla',
        'title': 'bla',
        'check_crs': check_crs,
        'uuid': publ_uuid,
    }
    filenames = fs_util.InputFiles(sent_paths=['abc.geojson'])
    workspace = 'test_abort_workspace'
    layername = 'test_abort_layer2'
    with app.app_context():
        input_chunk.save_layer_files_str(publ_uuid, filenames, check_crs)
    task_chain = chain(*[
        tasks_util.get_task_signature(workspace, layername, t, task_options, 'layername')
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
    # second one (and all others) is also failure in celery v5.2
    assert results[1].state == results_copy[1].state == 'FAILURE'
    assert results[2].state == results_copy[2].state == 'FAILURE'
    with app.app_context():
        input_chunk.delete_layer_by_uuid(publ_uuid)
