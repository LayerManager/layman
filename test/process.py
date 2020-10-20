import pytest
from multiprocessing import Process
import subprocess
import os

from src.layman import settings

from test.mock.liferay import run
from test import util


SUBPROCESSES = set()
LIFERAY_PORT = 8020

AUTHN_INTROSPECTION_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}/rest/test-oauth2/introspection?is_active=true"

LAYMAN_CELERY_QUEUE = 'temporary'

AUTHN_SETTINGS = {
    'LAYMAN_AUTHN_MODULES': 'layman.authn.oauth2',
    'OAUTH2_LIFERAY_INTROSPECTION_URL': AUTHN_INTROSPECTION_URL,
    'OAUTH2_LIFERAY_USER_PROFILE_URL': f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}/rest/test-oauth2/user-profile",
}


@pytest.fixture(scope="module")
def liferay_mock():
    server = Process(target=run, kwargs={
        'env_vars': {
        },
        'app_config': {
            'ENV': 'development',
            'SERVER_NAME': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}",
            'SESSION_COOKIE_DOMAIN': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}",
            'OAUTH2_USERS': {
                'test_rewe1': None,
                'test_rewo1': None,
                'test_rewe_rewo1': None,
                'test_rewe_rewo2': None,
                'testproxy': None,
                'testproxy2': None,
                'testmissingattr_authz': None,
                'testmissingattr_authz2': None,
            },
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
    util.wait_for_url(AUTHN_INTROSPECTION_URL, 20, 0.1)

    yield server

    server.terminate()
    server.join()


@pytest.fixture(scope="module", autouse=True)
def clear():
    yield
    while len(SUBPROCESSES) > 0:
        proc = next(iter(SUBPROCESSES))
        stop_process(proc)


def start_layman(env_vars=None):
    # first flush redis DB
    settings.LAYMAN_REDIS.flushdb()
    port = settings.LAYMAN_SERVER_NAME.split(':')[1]
    env_vars = env_vars or {}

    layman_env = os.environ.copy()
    layman_env.update(**env_vars)
    layman_env['LAYMAN_CELERY_QUEUE'] = LAYMAN_CELERY_QUEUE
    cmd = f'flask run --host=0.0.0.0 --port={port} --no-reload'
    layman_process = subprocess.Popen(cmd.split(), shell=False, stdin=None, env=layman_env)

    SUBPROCESSES.add(layman_process)
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest/current-user"
    util.wait_for_url(rest_url, 50, 0.1)

    celery_env = layman_env.copy()
    celery_env['LAYMAN_SKIP_REDIS_LOADING'] = 'true'
    cmd = f'python3 -m celery -Q {LAYMAN_CELERY_QUEUE} -A layman.celery_app worker --loglevel=info'
    celery_process = subprocess.Popen(cmd.split(), shell=False, stdin=None, env=layman_env, cwd='src')

    SUBPROCESSES.add(celery_process)

    return layman_process, celery_process


def stop_process(process):
    if not isinstance(process, tuple):
        process = (process,)
    for proc in process:
        proc.kill()
        SUBPROCESSES.remove(proc)
