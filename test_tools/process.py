from multiprocessing import Process
import subprocess
import os
import logging
import time
import pytest

from layman import settings, util as layman_util
from test_tools import util
from test_tools.mock.oauth2_provider import run


logger = logging.getLogger(__name__)

SUBPROCESSES = set()
OAUTH2_PROVIDER_MOCK_PORT = 8030

AUTHN_INTROSPECTION_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{OAUTH2_PROVIDER_MOCK_PORT}/rest/test-oauth2/introspection?is_active=true"

LAYMAN_CELERY_QUEUE = 'temporary'

AUTHN_SETTINGS = {
    'LAYMAN_AUTHN_MODULES': 'layman.authn.oauth2',
    'OAUTH2_INTROSPECTION_URL': AUTHN_INTROSPECTION_URL,
    'OAUTH2_USER_PROFILE_URL': f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{OAUTH2_PROVIDER_MOCK_PORT}/rest/test-oauth2/user-profile",
}

LAYMAN_SETTING = layman_util.SimpleStorage()
LAYMAN_DEFAULT_SETTINGS = AUTHN_SETTINGS
layman_start_counter = layman_util.SimpleCounter()


@pytest.fixture(scope="session")
def oauth2_provider_mock():
    server = Process(target=run, kwargs={
        'env_vars': {
        },
        'app_config': {
            'SERVER_NAME': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{OAUTH2_PROVIDER_MOCK_PORT}",
            'SESSION_COOKIE_DOMAIN': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{OAUTH2_PROVIDER_MOCK_PORT}",
            'OAUTH2_USERS': {
                'test_wfst_attr': None,
                'testmissingattr_authz': None,
                'testmissingattr_authz2': None,
                'test_public_workspace_variable_user': None,
                'test_delete_publications_owner': None,
                'test_delete_publications_deleter': None,
                'test_rest_soap_user': None,
                'test_check_user_wms' + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX: None,
                'test_dynamic_multi_ws1': None,
                'test_dynamic_multi_ws2': None,
                'test_dynamic_multi_ws3': None,
                'test_owner': None,
                'test_owner2': None,
                'test_not_owner': None,
                'dynamic_test_workspace_geoserver_proxy_user': None,
                'dynamic_test_workspace_geoserver_proxy_user_2': None,
                'dynamic_test_layer_patch_without_data_user': None,
                'test_fix_issuer_id_user': None,
                'layer_map_relation_user': None,
                'wrong_input_owner': None,
                'wrong_input_editor': None,
                'test_adjust_db_for_roles_ws': None,
                'test_adjust_db_for_roles_ws2': None,
                'test_access_rights_role_user1': None,
                'test_access_rights_application_owner': None,
                'test_access_rights_application_reader': None,
                'test_access_rights_application_other_user': None,
            },
        },
        'host': '0.0.0.0',
        'port': OAUTH2_PROVIDER_MOCK_PORT,
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
    print(f'\n\nEnsure_layman_session is ending - {layman_start_counter.get()}\n\n')


def ensure_layman_function(env_vars):
    if LAYMAN_SETTING.get() != env_vars:
        print(f'\nReally starting Layman LAYMAN_SETTING={LAYMAN_SETTING.get()}, settings={env_vars}')
        stop_process(list(SUBPROCESSES))
        start_layman(env_vars)
        LAYMAN_SETTING.set(env_vars)


# If you need fixture with different scope, create new fixture with such scope
@pytest.fixture(scope="class")
def ensure_layman():
    ensure_layman_function(LAYMAN_DEFAULT_SETTINGS)
    yield


@pytest.fixture(scope="module")
def ensure_layman_module():
    ensure_layman_function(LAYMAN_DEFAULT_SETTINGS)
    yield


def start_layman(env_vars=None):
    layman_start_counter.increase()
    print(f'\nstart_layman: Really starting Layman for the {layman_start_counter.get()}th time.')
    # first flush redis DB
    settings.LAYMAN_REDIS.flushdb()
    port = settings.LAYMAN_SERVER_NAME.split(':')[1]
    env_vars = env_vars or {}

    layman_env = os.environ.copy()
    layman_env.update(**env_vars)
    layman_env['LAYMAN_CELERY_QUEUE'] = LAYMAN_CELERY_QUEUE
    cmd = f'flask run --host=0.0.0.0 --port={port} --no-reload'
    # pylint: disable=consider-using-with
    layman_process = subprocess.Popen(cmd.split(), shell=False, stdin=None, env=layman_env)

    SUBPROCESSES.add(layman_process)
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest/current-user"
    util.wait_for_url(rest_url, 200, 0.1)

    celery_env = layman_env.copy()
    celery_env['LAYMAN_SKIP_REDIS_LOADING'] = 'true'
    cmd = f'python3 -m celery -A layman.celery_app worker -Q {LAYMAN_CELERY_QUEUE} --loglevel=info --concurrency=4'
    # pylint: disable=consider-using-with
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
