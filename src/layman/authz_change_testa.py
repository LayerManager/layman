import os
import pytest
import importlib
import time
import requests
from multiprocessing import Process

from test.run.layman import run


settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])


SUBPROCESSES = set()


@pytest.fixture(scope="module", autouse=True)
def stop_subprocesses():
    yield
    while len(SUBPROCESSES) > 0:
        proc = next(iter(SUBPROCESSES))
        stop_process(proc)


def start_layman(env_vars=None):
    # first flush redis DB
    settings.LAYMAN_REDIS.flushdb()
    port = settings.LAYMAN_SERVER_NAME.split(':')[1]
    env_vars = env_vars or {}
    layman_process = Process(target=run, kwargs={
        'env_vars': env_vars,
        'host': '0.0.0.0',
        'port': port,
        'debug': True,  # preserve error log in HTTP responses
        'load_dotenv': False,
        'options': {
            'use_reloader': False,
        },
    })
    layman_process.start()
    SUBPROCESSES.add(layman_process)
    time.sleep(1)
    return layman_process


def stop_process(process):
    process.terminate()
    process.join()
    SUBPROCESSES.remove(process)


def publish_layer(username, layername, file_paths):
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"

    r_url = f"{rest_url}/{username}/layers"
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        r = requests.post(r_url, files=[
            ('file', (os.path.basename(fp), open(fp, 'rb')))
            for fp in file_paths
        ], data={
            'name': layername,
        })
        assert r.status_code == 200
        print(r.json())
        layerinfo = r.json()[0]['name']
    finally:
        for fp in files:
            fp[0].close()

    r_url = f"{rest_url}/{username}/layers/{layername}"
    r = requests.get(r_url)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file', 'metadata']
    max_attempts = 20
    attempts = 1
    while not (r.status_code == 200 and all(
            'status' not in r.json()[k] for k in keys_to_check
    )):
        # print('waiting')
        time.sleep(0.5)
        r = requests.get(r_url)
        attempts += 1
        if attempts > max_attempts:
            raise Exception('Max attempts reached!')
    return layername


def assert_user_layers(username, layernames):
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/{username}/layers"
    r = requests.get(r_url)
    assert r.status_code == 200, f"r.status_code={r.status_code}\n{r.text}=r.text"
    layman_names = [li['name'] for li in r.json()]
    assert set(layman_names) == set(layernames), f"{r.text}=r.text"


def test_authz_change():
    test_user1 = 'test_authz_change1'
    layername1 = 'layer1'

    layman_process = start_layman({
        'LAYMAN_AUTHZ_MODULE': 'layman.authz.read_everyone_write_everyone',
    })

    assert_user_layers(test_user1, [])

    ln = publish_layer(test_user1, layername1, [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ])
    assert ln == layername1
    assert_user_layers(test_user1, [layername1])



    stop_process(layman_process)

    layman_process = start_layman({
        'LAYMAN_AUTHZ_MODULE': 'layman.authz.read_everyone_write_owner',
    })
    # print('REWE layman is up')
    stop_process(layman_process)
    # print('REWE layman is down')

    assert 1 == 2

