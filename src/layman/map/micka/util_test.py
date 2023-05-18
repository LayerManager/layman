import os
import filecmp
import difflib
import sys
import pytest

del sys.modules['layman']

from layman import app, settings
from layman.common.metadata import PROPERTIES as COMMON_PROPERTIES, prop_equals
from layman.common.micka import util as common_util
from test_tools.util import url_for
from .csw import _get_property_values, METADATA_PROPERTIES


@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    yield client


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.mark.usefixtures('app_context', 'ensure_layman', 'client')
def test_fill_template():
    xml_path = 'tmp/record-template.xml'
    try:
        os.remove(xml_path)
    except OSError:
        pass
    file_object = common_util.fill_xml_template_as_pretty_file_object('src/layman/map/micka/record-template.xml',
                                                                      _get_property_values(), METADATA_PROPERTIES)
    with open(xml_path, 'wb') as out:
        out.write(file_object.read())

    def get_diff(path1, path2):
        with open(path1, encoding="utf-8") as file1, open(path2, encoding="utf-8") as file2:
            diff = difflib.unified_diff(file1.readlines(), file2.readlines())
        return f"diff={''.join(diff)}"

    expected_path = 'src/layman/map/micka/util_test_filled_template.xml'
    assert filecmp.cmp(xml_path, expected_path, shallow=False), get_diff(xml_path, expected_path)


def test_parse_md_properties():
    xml_path = 'src/layman/map/rest_test_filled_template.xml'
    with open(xml_path, 'r', encoding="utf-8") as xml_file:
        props = common_util.parse_md_properties(xml_file, [
            'abstract',
            'extent',
            'graphic_url',
            'identifier',
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
        ], METADATA_PROPERTIES)
    with app.app_context():
        expected = {
            'md_file_identifier': 'm-91147a27-1ff4-4242-ba6d-faffb92224c6',
            'md_organisation_name': None,
            'organisation_name': None,
            'md_date_stamp': '2007-05-25',
            'reference_system': ['EPSG:3857'],
            'title': 'World places and boundaries',
            'publication_date': '2007-05-25',
            'identifier': {
                'identifier': url_for('rest_workspace_map.get', workspace='testuser1', mapname='svet', internal=False),
                'label': 'svet',
            },
            'abstract': 'World places and boundaries abstract',
            'graphic_url': url_for('rest_workspace_map_thumbnail.get', workspace='testuser1', mapname='svet',
                                   internal=False),
            'extent': [-35, -48.5, 179, 81.5],
            'map_endpoint': url_for('rest_workspace_map.get', workspace='testuser1', mapname='svet',
                                    internal=False),
            'map_file_endpoint': url_for('rest_workspace_map_file.get', workspace='testuser1', mapname='svet',
                                         internal=False),
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
    for k, value in props.items():
        equals_fn = COMMON_PROPERTIES[k].get('equals_fn', None)
        assert prop_equals(value, expected[k],
                           equals_fn), f"Values of property {k} do not equal: {value} != {expected[k]}"


@pytest.mark.usefixtures('app_context', 'ensure_layman', 'client')
def test_fill_xml_template():
    with app.app_context():
        xml_file_object = common_util.fill_xml_template_as_pretty_file_object('src/layman/map/micka/record-template.xml', {
            'md_file_identifier': 'm-91147a27-1ff4-4242-ba6d-faffb92224c6',
            'md_organisation_name': None,
            'md_date_stamp': '2007-05-25',
            'reference_system': ['EPSG:3857'],
            'title': 'World places and boundaries',
            'publication_date': '2007-05-25',
            'identifier': {
                'identifier': url_for('rest_workspace_map.get', workspace='testuser1', mapname='svet', internal=False),
                'label': 'svet',
            },
            'abstract': 'World places and boundaries abstract',
            'organisation_name': None,
            'graphic_url': url_for('rest_workspace_map_thumbnail.get', workspace='testuser1', mapname='svet',
                                   internal=False),
            'extent': [-35, -48.5, 179, 81.5],
            'map_endpoint': url_for('rest_workspace_map.get', workspace='testuser1', mapname='svet',
                                    internal=False),
            'map_file_endpoint': url_for('rest_workspace_map_file.get', workspace='testuser1', mapname='svet',
                                         internal=False),
            'md_language': 'cze',
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
        }, METADATA_PROPERTIES)

    expected_path = 'src/layman/map/micka/record-template-filled.xml'
    with open(expected_path, encoding="utf-8") as file:
        expected_lines = file.readlines()
    lines = [line.decode('utf-8') for line in xml_file_object.readlines()]
    # print(f"FILE:\n{''.join(lines)}")
    diff_lines = list(difflib.unified_diff(expected_lines, lines))
    assert len(diff_lines) == 0, f"DIFF LINES:\n{''.join(diff_lines)}"
