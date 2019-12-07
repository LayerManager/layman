from multiprocessing import Process
import pytest
import time
import os
import filecmp
import difflib

import sys
del sys.modules['layman']

from layman import app as app
from layman import settings
from layman.layer.filesystem.metadata import _get_template_values

from . import util


@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    # print('before Process(target=app.run, kwargs={...')
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': settings.LAYMAN_SERVER_NAME.split(':')[1],
        'debug': False,
    })
    # print('before server.start()')
    server.start()
    time.sleep(1)

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    yield client

    # print('before server.terminate()')
    server.terminate()
    # print('before server.join()')
    server.join()


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.mark.usefixtures('app_context')
def test_fill_template(client):
    xml_path = 'tmp/metadata-template.xml'
    try:
        os.remove(xml_path)
    except OSError:
        pass
    file_object = util.fill_template('src/layman/layer/filesystem/metadata-template.xml', _get_template_values())
    with open(xml_path, 'wb') as out:
        out.write(file_object.read())

    def get_diff(p1, p2):
        diff = difflib.unified_diff(open(p1).readlines(), open(p2).readlines())
        return f"diff={''.join(diff)}"

    expected_path = 'src/layman/common/metadata/util_test_filled_template.xml'
    assert filecmp.cmp(xml_path, expected_path, shallow=False), get_diff(xml_path, expected_path)


