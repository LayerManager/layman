from multiprocessing import Process
import pytest
import time
import os
import filecmp
import difflib

import sys
del sys.modules['layman']

from layman import uuid
from layman import app as app
from layman import settings
from layman.map import MAP_TYPE
from .csw import _get_template_values, METADATA_PROPERTIES
from layman.common.metadata import PROPERTIES as COMMON_PROPERTIES, prop_equals

from layman.common.micka import util as common_util


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
    xml_path = 'tmp/record-template.xml'
    try:
        os.remove(xml_path)
    except OSError:
        pass
    file_object = common_util.fill_template('src/layman/map/micka/record-template.xml', _get_template_values())
    with open(xml_path, 'wb') as out:
        out.write(file_object.read())

    def get_diff(p1, p2):
        diff = difflib.unified_diff(open(p1).readlines(), open(p2).readlines())
        return f"diff={''.join(diff)}"

    expected_path = 'src/layman/map/micka/util_test_filled_template.xml'
    assert filecmp.cmp(xml_path, expected_path, shallow=False), get_diff(xml_path, expected_path)


def test_parse_md_properties():
    xml_path = 'src/layman/map/rest_test_filled_template.xml'
    with open(xml_path, 'r') as xml_file:
        props = common_util.parse_md_properties(xml_file, [
           'abstract',
           'extent',
           'graphic_url',
           'identifier',
           'language',
           'map_endpoint',
           'map_file_endpoint',
           'md_date_stamp',
           'md_file_identifier',
           'md_organisation_name',
           'organisation_name',
           'publication_date',
           'reference_system',
           'title',
           'operates_on',
           'language',
        ], METADATA_PROPERTIES)
    expected = {
        'md_file_identifier': 'm-91147a27-1ff4-4242-ba6d-faffb92224c6',
        'md_organisation_name': None,
        'organisation_name': None,
        'language': None,
        'md_date_stamp': '2007-05-25',
        'reference_system': [3857],
        'title': 'World places and boundaries',
        'publication_date': '2007-05-25',
        'identifier': {
            'identifier': 'http://layman_test_run_1:8000/rest/testuser1/maps/svet',
            'label': 'svet',
        },
        'abstract': 'World places and boundaries abstract',
        'graphic_url': 'http://layman_test_run_1:8000/rest/testuser1/maps/svet/thumbnail',
        'extent': [-35, -48.5, 179, 81.5],
        'map_endpoint': 'http://layman_test_run_1:8000/rest/testuser1/maps/svet',
        'map_file_endpoint': 'http://layman_test_run_1:8000/rest/testuser1/maps/svet/file',
        'operates_on': [
            {
                'xlink:href': 'http://localhost:3080/csw?SERVICE=CSW&VERSION=2.0.2&REQUEST=GetRecordById&OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&ID=m-39cc8994-adbc-427a-8522-569eb7e691b2#_m-39cc8994-adbc-427a-8522-569eb7e691b2',
                'xlink:title': 'hranice',
            },
            {
                'xlink:href': 'http://localhost:3080/csw?SERVICE=CSW&VERSION=2.0.2&REQUEST=GetRecordById&OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&ID=m-fb48a6e3-f36c-43fd-a885-ae7de82b3924#_m-fb48a6e3-f36c-43fd-a885-ae7de82b3924',
                'xlink:title': 'mista',
            },
        ],
    }
    assert set(props.keys()) == set(expected.keys())
    for k in props.keys():
        equals_fn = COMMON_PROPERTIES[k].get('equals_fn', None)
        assert prop_equals(props[k], expected[k], equals_fn), f"Values of property {k} do not equal: {props[k]} != {expected[k]}"


