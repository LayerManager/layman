from datetime import date
import json
import time
import sys
import pytest

del sys.modules['layman']

from layman import app, settings, celery as celery_util
from layman.common.metadata import prop_equals_strict, PROPERTIES
from layman.util import SimpleCounter
from test_tools.util import url_for
from . import util

TODAY_DATE = date.today().strftime('%Y-%m-%d')

METADATA_PROPERTIES = {
    'abstract',
    'extent',
    'graphic_url',
    'identifier',
    'map_endpoint',
    'map_file_endpoint',
    'operates_on',
    'organisation_name',
    'publication_date',
    'reference_system',
    'revision_date',
    'title',
}

METADATA_PROPERTIES_EQUAL = METADATA_PROPERTIES

publication_counter = SimpleCounter()


def wait_till_ready(workspace, mapname):
    chain_info = util.get_map_chain(workspace, mapname)
    while chain_info is not None and not celery_util.is_chain_ready(chain_info):
        time.sleep(0.1)
        chain_info = util.get_map_chain(workspace, mapname)


def check_metadata(client, workspace, mapname, props_equal, expected_values):
    with app.app_context():
        rest_path = url_for('rest_workspace_map_metadata_comparison.get', workspace=workspace, mapname=mapname)
        response = client.get(rest_path)
        assert response.status_code == 200, response.get_json()
        resp_json = response.get_json()
        assert METADATA_PROPERTIES == set(resp_json['metadata_properties'].keys())
        # for k, v in resp_json['metadata_properties'].items():
        #     print(f"'{k}': {json.dumps(list(v['values'].values())[0], indent=2)},")
        for key, value in resp_json['metadata_properties'].items():
            assert value['equal_or_null'] == (
                key in props_equal), f"Metadata property values have unexpected 'equal_or_null' value: {key}: {json.dumps(value, indent=2)}, sources: {json.dumps(resp_json['metadata_sources'], indent=2)}"
            assert value['equal'] == (
                key in props_equal), f"Metadata property values have unexpected 'equal' value: {key}: {json.dumps(value, indent=2)}, sources: {json.dumps(resp_json['metadata_sources'], indent=2)}"
            # print(f"'{k}': {json.dumps(list(v['values'].values())[0], indent=2)},")
            if key in expected_values:
                vals = list(value['values'].values())
                vals.append(expected_values[key])
                assert prop_equals_strict(vals, equals_fn=PROPERTIES[key].get('equals_fn',
                                                                              None)), \
                    f"Property {key} has unexpected values {json.dumps(vals, indent=2)}"


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
