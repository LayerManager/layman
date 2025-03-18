import os
import filecmp
import difflib
import sys
import pytest

del sys.modules['layman']

from layman import app, settings, util as layman_util
from layman.common.micka import util as common_util, MickaNames
from layman.common.metadata import PROPERTIES as COMMON_PROPERTIES, prop_equals
from layman.layer.geoserver import wms, wfs
from test_tools.util import url_for
from . import csw as csw_util


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
    workspace = 'browser'
    layer = 'layer'
    layer_uuid = 'ca238200-8200-1a23-9399-42c9fca53542'
    file_object = common_util.fill_xml_template_as_pretty_file_object('src/layman/layer/micka/record-template.xml',
                                                                      {
                                                                          'md_file_identifier': MickaNames(uuid=layer_uuid).metadata_uuid,
                                                                          'md_language': None,
                                                                          'md_date_stamp': '2007-05-25',
                                                                          'reference_system': ['EPSG:3857', 'EPSG:4326'],
                                                                          'title': 'CORINE - Krajinný pokryv CLC 90',
                                                                          'publication_date': '2007-05-25',
                                                                          'revision_date': '2008-05-25',
                                                                          'identifier': {
                                                                              'identifier': 'http://www.env.cz/data/corine/1990',
                                                                              'label': 'MZP-CORINE',
                                                                          },
                                                                          'abstract': None,
                                                                          'graphic_url': layman_util.url_for(
                                                                              'rest_workspace_layer_thumbnail.get',
                                                                              workspace=workspace,
                                                                              layername=layer),
                                                                          'extent': [11.87, 48.12, 19.13, 51.59],
                                                                          'temporal_extent': ['2022-03-16T00:00:00.000Z',
                                                                                              '2022-03-19T00:00:00.000Z', ],
                                                                          'wms_url': f"{wms.add_capabilities_params_to_url('http://www.env.cz/corine/data/download.zip')}&LAYERS=l_{layer_uuid}",
                                                                          'wfs_url': f"{wfs.add_capabilities_params_to_url('http://www.env.cz/corine/data/download.zip')}&LAYERS=l_{layer_uuid}",
                                                                          'layer_endpoint': layman_util.url_for(
                                                                              'rest_workspace_layer.get',
                                                                              workspace=workspace,
                                                                              layername=layer),
                                                                          'spatial_resolution': {
                                                                              'scale_denominator': None,
                                                                          },
                                                                          'language': [],
                                                                          'md_organisation_name': None,
                                                                          'organisation_name': None,
                                                                      }, csw_util.METADATA_PROPERTIES)
    with open(xml_path, 'wb') as out:
        out.write(file_object.read())

    def get_diff(path1, path2):
        with open(path1, encoding="utf-8") as file1, open(path2, encoding="utf-8") as file2:
            diff = difflib.unified_diff(file1.readlines(), file2.readlines())
        return f"diff={''.join(diff)}"

    expected_path = 'src/layman/layer/micka/util_test_filled_template.xml'
    assert filecmp.cmp(xml_path, expected_path, shallow=False), get_diff(xml_path, expected_path)


def test_parse_md_properties():
    xml_path = 'src/layman/layer/micka/util_test_filled_template.xml'
    with open(xml_path, 'r', encoding="utf-8") as xml_file:
        props = common_util.parse_md_properties(xml_file, [
            'abstract',
            'extent',
            'graphic_url',
            'identifier',
            'layer_endpoint',
            'language',
            'md_date_stamp',
            'md_file_identifier',
            'md_organisation_name',
            'organisation_name',
            'publication_date',
            'reference_system',
            'spatial_resolution',
            'title',
            'wfs_url',
            'wms_url',
        ], csw_util.METADATA_PROPERTIES)
    with app.app_context():
        expected = {
            'md_file_identifier': 'm-ca238200-8200-1a23-9399-42c9fca53542',
            'md_date_stamp': '2007-05-25',
            'md_organisation_name': None,
            'organisation_name': None,
            'spatial_resolution': {
                'scale_denominator': None,
            },
            'language': [],
            'reference_system': [4326, 3857],
            'title': 'CORINE - Krajinný pokryv CLC 90',
            'publication_date': '2007-05-25',
            'identifier': {
                'identifier': 'http://www.env.cz/data/corine/1990',
                'label': 'MZP-CORINE',
            },
            'abstract': None,
            'graphic_url': url_for('rest_workspace_layer_thumbnail.get', workspace='browser', layername='layer',
                                   internal=False),
            'extent': [11.87, 48.12, 19.13, 51.59],
            'wms_url': 'http://www.env.cz/corine/data/download.zip',
            'wfs_url': 'http://www.env.cz/corine/data/download.zip',
            'layer_endpoint': url_for('rest_workspace_layer.get', workspace='browser', layername='layer',
                                      internal=False),
        }
    assert set(props.keys()) == set(expected.keys())
    for k, value in props.items():
        equals_fn = COMMON_PROPERTIES[k].get('equals_fn', None)
        assert prop_equals(value, expected[k],
                           equals_fn), f"Values of property {k} do not equal: {value} != {expected[k]}"


@pytest.mark.usefixtures('app_context', 'ensure_layman', 'client')
def test_fill_xml_template():
    xml_file_object = common_util.fill_xml_template_as_pretty_file_object('src/layman/layer/micka/record-template.xml',
                                                                          {
                                                                              'md_file_identifier': 'm-abc',
                                                                              'md_language': 'eng',
                                                                              'md_organisation_name': 'My Metadata Organization',
                                                                              'md_date_stamp': '2007-01-22',
                                                                              'reference_system': ['EPSG:4326', 'EPSG:5514'],
                                                                              'title': 'My title',
                                                                              'publication_date': '2006-12-12',
                                                                              'identifier': {
                                                                                  'identifier': 'id-abc',
                                                                                  'label': 'Dataset ABC',
                                                                              },
                                                                              'abstract': None,
                                                                              'organisation_name': 'My Organization',
                                                                              'graphic_url': 'https://example.com/myimage.png',
                                                                              'spatial_resolution': {
                                                                                  'ground_sample_distance': {
                                                                                      'value': 123.45,
                                                                                      'uom': "m",
                                                                                  }
                                                                              },
                                                                              'language': ['cze', 'eng'],
                                                                              'extent': [11.87, 48.12, 19.13, 51.59],
                                                                              'wms_url': 'https://example.com/wms',
                                                                              'wfs_url': 'https://example.com/wfs',
                                                                              'layer_endpoint': 'https://example.com/layer_endpoint',
                                                                          }, csw_util.METADATA_PROPERTIES)

    expected_path = 'src/layman/layer/micka/record-template-filled.xml'
    with open(expected_path, encoding="utf-8") as file:
        expected_lines = file.readlines()
    lines = [line.decode('utf-8') for line in xml_file_object.readlines()]
    # print(f"FILE:\n{''.join(lines)}")
    diff_lines = list(difflib.unified_diff(expected_lines, lines))
    assert len(diff_lines) == 0, f"DIFF LINES:\n{''.join(diff_lines)}"
