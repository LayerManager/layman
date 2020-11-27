import pytest
from multiprocessing import Process
import subprocess
import os
import redis
import logging
import time

from layman import settings

from test.mock.liferay import run
from test import util


logger = logging.getLogger(__name__)

SUBPROCESSES = set()
LIFERAY_PORT = 8020

AUTHN_INTROSPECTION_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}/rest/test-oauth2/introspection?is_active=true"

LAYMAN_CELERY_QUEUE = 'temporary'
LAYMAN_REDIS_URL = 'redis://redis:6379/12'
LAYMAN_REDIS = redis.Redis.from_url(LAYMAN_REDIS_URL, encoding="utf-8", decode_responses=True)


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
                'test_gs_rules_user': None,
                'testproxy': None,
                'testproxy2': None,
                'testmissingattr': None,
                'testmissingattr_authz': None,
                'testmissingattr_authz2': None,
                'test_authorize_decorator_user': None,
                'test_patch_gs_access_rights_user': None,
                'test_map_with_unauthorized_layer_user1': None,
                'test_map_with_unauthorized_layer_user2': None,
                'test_public_workspace_variable_user': None,
                'test_wms_ows_proxy_user': None,
                'test_get_publication_info_user': None,
                'test_get_publication_info_without_user': None,
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


@pytest.fixture(scope="module")
def ensure_layman():
    print(f'\nEnsure layman is starting')
    processes = start_layman(AUTHN_SETTINGS)
    yield
    stop_process(processes)
    print(f'\nEnsure layman is ending')


def start_layman(env_vars=None):
    # first flush redis DB
    LAYMAN_REDIS.flushdb()
    port = settings.LAYMAN_SERVER_NAME.split(':')[1]
    env_vars = env_vars or {}

    layman_env = os.environ.copy()
    layman_env.update(**env_vars)
    layman_env['LAYMAN_CELERY_QUEUE'] = LAYMAN_CELERY_QUEUE
    layman_env['LAYMAN_REDIS_URL'] = LAYMAN_REDIS_URL
    cmd = f'flask run --host=0.0.0.0 --port={port} --no-reload'
    layman_process = subprocess.Popen(cmd.split(), shell=False, stdin=None, env=layman_env)

    SUBPROCESSES.add(layman_process)
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest/current-user"
    util.wait_for_url(rest_url, 200, 0.1)

    celery_env = layman_env.copy()
    celery_env['LAYMAN_SKIP_REDIS_LOADING'] = 'true'
    cmd = f'python3 -m celery -Q {LAYMAN_CELERY_QUEUE} -A layman.celery_app worker --loglevel=info --concurrency=4'
    celery_process = subprocess.Popen(cmd.split(), shell=False, stdin=None, env=layman_env, cwd='src')

    SUBPROCESSES.add(celery_process)

    return layman_process, celery_process


def stop_process(process):
    if not isinstance(process, tuple):
        process = (process,)
    for proc in process:
        proc.kill()
        SUBPROCESSES.remove(proc)
    time.sleep(1)
