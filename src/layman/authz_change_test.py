import os
import pytest
import importlib
from multiprocessing import Process
import time
import requests
import subprocess
from test.mock.liferay import run


settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])

LIFERAY_PORT = 8020

SUBPROCESSES = set()
ISS_URL_HEADER = 'AuthorizationIssUrl'
TOKEN_HEADER = 'Authorization'


@pytest.fixture(scope="module")
def liferay_mock():
    server = Process(target=run, kwargs={
        'env_vars': {
        },
        'app_config': {
            'ENV': 'development',
            'SERVER_NAME': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}",
            'SESSION_COOKIE_DOMAIN': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}",
        },
        'host': '0.0.0.0',
        'port': LIFERAY_PORT,
        'debug': True,  # preserve error log in HTTP responses
        'load_dotenv': False,
        'options': {
            'use_reloader': False,
        },
    })
    server.start()
    time.sleep(1)

    yield server

    server.terminate()
    server.join()


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

    new_env = os.environ.copy()
    new_env.update(**env_vars)
    cmd = f'flask run --host=0.0.0.0 --port={port} --no-reload'
    layman_process = subprocess.Popen(cmd.split(), shell=False, stdin=None, env=new_env)

    SUBPROCESSES.add(layman_process)
    time.sleep(1)
    return layman_process


def stop_process(process):
    process.kill()
    SUBPROCESSES.remove(process)


def publish_layer(username, layername, file_paths, headers=None):
    headers = headers or {}
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
        }, headers=headers)
        assert r.status_code == 200, r.text
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
        time.sleep(0.5)
        r = requests.get(r_url)
        attempts += 1
        if attempts > max_attempts:
            raise Exception('Max attempts reached!')
    return layername


def delete_layer(username, layername, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"

    r_url = f"{rest_url}/{username}/layers/{layername}"
    r = requests.delete(r_url, headers=headers)
    assert r.status_code == 200, r.text


def assert_user_layers(username, layernames):
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/{username}/layers"
    r = requests.get(r_url)
    assert r.status_code == 200, f"r.status_code={r.status_code}\n{r.text}=r.text"
    layman_names = [li['name'] for li in r.json()]
    assert set(layman_names) == set(layernames), f"{r.text}=r.text"


def assert_username_not_yet_used(username):
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/{username}/layers"
    r = requests.get(r_url)
    assert r.status_code == 404, f"r.status_code={r.status_code}\n{r.text}=r.text"
    assert r.json()['code'] == 40


def reserve_username(username, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/current-user?adjust_username=true"
    r = requests.patch(r_url, headers=headers)
    assert r.status_code == 200, r.text
    claimed_username = r.json()['username']
    assert claimed_username == username


def test_authz_change(liferay_mock):
    test_user1 = 'test_authz_change1'
    layername1 = 'layer1'

    oauth_settings = {
        'LAYMAN_AUTHN_MODULES': 'layman.authn.oauth2',
        'OAUTH2_LIFERAY_INTROSPECTION_URL': f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}/rest/test-oauth2/introspection?is_active=true",
        'OAUTH2_LIFERAY_USER_PROFILE_URL': f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}/rest/test-oauth2/user-profile",
    }

    layman_process = start_layman(dict({
        'LAYMAN_AUTHZ_MODULE': 'layman.authz.read_everyone_write_owner',
    }, **oauth_settings))
    authn_headers1 = {
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': f'Bearer {test_user1}',
    }
    reserve_username(test_user1, headers=authn_headers1)

    ln = publish_layer(test_user1, layername1, [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ], headers=authn_headers1)
    assert ln == layername1
    assert_user_layers(test_user1, [layername1])

    stop_process(layman_process)

    test_user2 = 'test_authz_change2'
    layername2 = 'layer2'
    layman_process = start_layman(dict({
        'LAYMAN_AUTHZ_MODULE': 'layman.authz.read_everyone_write_owner',
    }, **oauth_settings))
    authn_headers2 = {
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': f'Bearer {test_user2}',
    }
    reserve_username(test_user2, headers=authn_headers2)

    ln = publish_layer(test_user2, layername2, [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ], headers=authn_headers2)
    assert ln == layername2
    assert_user_layers(test_user2, [layername2])

    delete_layer(test_user1, layername1, headers=authn_headers1)
    delete_layer(test_user2, layername2, headers=authn_headers2)

    stop_process(layman_process)
