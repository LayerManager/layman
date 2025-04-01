from multiprocessing import Process
import time
from urllib.parse import urljoin
import requests
import pytest

from layman import app, LaymanError
from layman import settings
from layman.layer.layer_class import Layer
from test_tools import process, process_client
from test_tools.mock.micka import run
from .csw import get_layer_info, delete_layer

MICKA_PORT = 8020
TEST_WORKSPACE = 'testuser_micka'
TEST_LAYER = 'ne_110m_admin_0_countries'


@pytest.fixture(scope='module')
# pylint: disable=unused-argument
def provide_layer(ensure_layman_module):
    workspace = TEST_WORKSPACE
    layername = TEST_LAYER
    process_client.publish_workspace_layer(workspace, layername)
    with app.app_context():
        layer = Layer(layer_tuple=(workspace, layername))

    yield layer
    process.ensure_layman_function(None)
    process_client.delete_workspace_layer(workspace, layername)


class TestBrokenMicka:
    @staticmethod
    def create_server(port):
        server = Process(target=run, kwargs={
            'env_vars': {
                'CSW_GET_RESP_CODE': '500'
            },
            'app_config': {
                'SERVER_NAME': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{port}",
                'SESSION_COOKIE_DOMAIN': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{port}",
            },
            'host': '0.0.0.0',
            'port': port,
            'debug': True,  # preserve error log in HTTP responses
            'load_dotenv': False,
            'options': {
                'use_reloader': False,
            },
        })
        return server

    @pytest.fixture(scope="module")
    def broken_micka(self):
        server = self.create_server(MICKA_PORT)
        server.start()
        time.sleep(1)

        yield server

        server.terminate()
        server.join()

    @staticmethod
    @pytest.fixture(autouse=True)
    def broken_micka_url(broken_micka):
        # pylint: disable=unused-argument
        csw_url = settings.CSW_URL
        settings.CSW_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{MICKA_PORT}/csw"
        yield
        settings.CSW_URL = csw_url

    @staticmethod
    def test_delete_layer_broken_micka(provide_layer):
        with pytest.raises(LaymanError) as exc_info:
            delete_layer(provide_layer)
        assert exc_info.value.code == 38

    @staticmethod
    def test_get_layer_info_broken_micka():
        with app.app_context():
            layer_info = get_layer_info('abc', 'abcd')
        assert layer_info == {}


class TestNoMicka:
    @staticmethod
    @pytest.fixture(autouse=True)
    def no_micka_url():
        csw_url = settings.CSW_URL
        settings.CSW_URL = f"http://unexistinghost/cswa"
        yield
        settings.CSW_URL = csw_url

    @staticmethod
    def test_delete_layer_no_micka(provide_layer):
        with pytest.raises(LaymanError) as exc_info:
            with app.app_context():
                delete_layer(provide_layer)
        assert exc_info.value.code == 38

    @staticmethod
    def test_get_layer_info_no_micka():
        with app.app_context():
            layer_info = get_layer_info('abc', 'abcd')
        assert layer_info == {}


@pytest.mark.usefixtures('ensure_layman_module')
def test_patch_layer_without_metadata(provide_layer):
    with app.app_context():
        delete_layer(provide_layer)
    process_client.patch_workspace_layer(provide_layer.workspace, provide_layer.name,
                                         file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',],
                                         title='patched layer'
                                         )


@pytest.mark.usefixtures('ensure_layman')
def test_public_metadata(provide_layer):
    muuid = provide_layer.micka_ids.id
    micka_url = urljoin(settings.CSW_URL, "./")
    response = requests.get(micka_url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    response.raise_for_status()
    assert muuid in response.text, f"Metadata record {muuid} is not public!"
