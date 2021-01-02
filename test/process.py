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
LIFERAY_PORT = 8030

AUTHN_INTROSPECTION_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}/rest/test-oauth2/introspection?is_active=true"

LAYMAN_CELERY_QUEUE = 'temporary'
LAYMAN_REDIS_URL = 'redis://redis:6379/12'
LAYMAN_REDIS = redis.Redis.from_url(LAYMAN_REDIS_URL, encoding="utf-8", decode_responses=True)


AUTHN_SETTINGS = {
    'LAYMAN_AUTHN_MODULES': 'layman.authn.oauth2',
    'OAUTH2_LIFERAY_INTROSPECTION_URL': AUTHN_INTROSPECTION_URL,
    'OAUTH2_LIFERAY_USER_PROFILE_URL': f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}/rest/test-oauth2/user-profile",
}

LAYMAN_SETTING = {}
LAYMAN_DEFAULT_SETTINGS = AUTHN_SETTINGS
LAYMAN_START_COUNT = 0


@pytest.fixture(scope="session")
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
                'test_delete_publications_owner': None,
                'test_delete_publications_deleter': None,
                'test_get_publication_infos_user_owner': None,
                'test_rest_soap_user': None,
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


@pytest.fixture(scope='session', autouse=True)
def ensure_layman_session():
    print(f'\n\nEnsure_layman_session is starting\n\n')
    yield
    stop_process(list(SUBPROCESSES))
    print(f'\n\nEnsure_layman_session is ending - {LAYMAN_START_COUNT}\n\n')


def ensure_layman_function(env_vars):
    global LAYMAN_SETTING
    if LAYMAN_SETTING != env_vars:
        print(f'\nReally starting Layman LAYMAN_SETTING={LAYMAN_SETTING}, settings={env_vars}')
        stop_process(list(SUBPROCESSES))
        start_layman(env_vars)
        LAYMAN_SETTING = env_vars


@pytest.fixture(scope="class")
def ensure_layman():
    ensure_layman_function(LAYMAN_DEFAULT_SETTINGS)
    yield


def start_layman(env_vars=None):
    global LAYMAN_START_COUNT
    LAYMAN_START_COUNT = LAYMAN_START_COUNT + 1
    print(f'\nstart_layman: Really starting Layman for the {LAYMAN_START_COUNT}th time.')
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

    return [layman_process, celery_process, ]


def stop_process(process):
    if not isinstance(process, list):
        process = {process, }
    for proc in process:
        proc.kill()
        SUBPROCESSES.remove(proc)
    time.sleep(1)
