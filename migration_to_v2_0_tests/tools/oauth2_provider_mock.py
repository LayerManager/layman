from multiprocessing import Process

from test_tools.mock.oauth2_provider import run
from .util import wait_for_url


PORT = '8123'
AUTHN_INTROSPECTION_URL = f"http://localhost:{PORT}/rest/test-oauth2/introspection?is_active=true"


class OAuth2ProviderMock():
    def __init__(self):
        self.server = None

    def __enter__(self):
        self.server = Process(target=run, kwargs={
            'env_vars': {
            },
            'app_config': {
                'SERVER_NAME': f"host.docker.internal:{PORT}",
                'SESSION_COOKIE_DOMAIN': f"host.docker.internal:{PORT}",
                'OAUTH2_USERS': {
                    'test_migrate_2_user_1': None,
                },
            },
            'host': '0.0.0.0',
            'port': PORT,
            'debug': True,  # preserve error log in HTTP responses
            'load_dotenv': False,
            'options': {
                'use_reloader': False,
            },
        })
        self.server.start()
        wait_for_url(AUTHN_INTROSPECTION_URL, 20, 0.1)

    def __exit__(self, exc_type, exc_value, traceback):
        self.server.terminate()
        self.server.join()
