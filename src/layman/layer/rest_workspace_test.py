from contextlib import ExitStack
from datetime import date
import io
import json
import os
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import logging
import sys
import requests
import pytest

del sys.modules['layman']

from geoserver.util import get_feature_type
from layman import app
from layman import settings
from layman.layer.filesystem.thumbnail import get_layer_thumbnail_path
from layman import uuid, names
from layman.layer.geoserver import wms as geoserver_wms, sld as geoserver_sld
from layman import celery as celery_util
from layman.common.metadata import prop_equals_strict, PROPERTIES
from layman.util import SimpleCounter, get_publication_uuid
from test_tools.data import wfs as data_wfs
from test_tools.util import url_for, url_for_external
from test_tools import flask_client, process_client
from . import util, LAYER_TYPE
from .geoserver.util import wms_proxy, DEFAULT_INTERNAL_DB_STORE

logger = logging.getLogger(__name__)


TODAY_DATE = date.today().strftime('%Y-%m-%d')

EXP_REFERENCE_SYSTEMS = [3034, 3035, 3059, 3857, 4326, 5514, 32633, 32634, ]

METADATA_PROPERTIES = {
    'abstract',
    'extent',
    'graphic_url',
    'identifier',
    'layer_endpoint',
    'language',
    'organisation_name',
    'publication_date',
    'reference_system',
    'revision_date',
    'spatial_resolution',
    'temporal_extent',
    'title',
    'wfs_url',
    'wms_url',
}

METADATA_PROPERTIES_EQUAL = METADATA_PROPERTIES

MIN_GEOJSON = """
{
  "type": "Feature",
  "geometry": null,
  "properties": null
}
"""

publication_counter = SimpleCounter()


def check_metadata(client, workspace, layername, props_equal, expected_values):
    with app.app_context():
        rest_path = url_for('rest_workspace_layer_metadata_comparison.get', workspace=workspace, layername=layername)
        response = client.get(rest_path)
        assert response.status_code == 200, response.get_json()
        resp_json = response.get_json()
        assert METADATA_PROPERTIES == set(resp_json['metadata_properties'].keys())
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
                                                                              None)), f"Property {key} has unexpected values {json.dumps(value, indent=2)}"


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


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_wrong_value_of_workspace(client):
    workspaces = [' ', '2a', 'ě', ';', '?', 'ABC']
    for workspace in workspaces:
        response = client.post(url_for('rest_workspace_layers.post', workspace=workspace))
        resp_json = response.get_json()
        # print('username', username)
        # print(resp_json)
        assert response.status_code == 400
        assert resp_json['code'] == 2
        assert resp_json['detail']['parameter'] == 'workspace'


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_layman_gs_user_conflict(client):
    """Tests that Layman detects that reserved username is in conflict with LAYMAN_GS_USER.

    See https://github.com/LayerManager/layman/pull/97
    """

    workspace = settings.LAYMAN_GS_USER
    layername = 'layer1'
    rest_path = url_for('rest_workspace_layers.post', workspace=workspace)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson',
    ]
    for file_path in file_paths:
        assert os.path.isfile(file_path)
    with ExitStack() as stack:
        files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
        response = client.post(rest_path, data={
            'file': files,
            'name': layername,
        })
    resp_json = response.get_json()
    assert response.status_code == 409
    assert resp_json['code'] == 41


@pytest.mark.usefixtures('ensure_layman')
def test_wrong_value_of_layername(client):
    workspace = 'test_wrong_value_of_layername_workspace'
    layername = 'layer1'
    # publish and delete layer to ensure that username exists
    flask_client.publish_layer(workspace, layername, client)
    flask_client.delete_layer(workspace, layername, client)
    layernames = [' ', 'ě', ';', '?', 'ABC']
    for layername in layernames:
        with app.app_context():
            response = client.get(url_for('rest_workspace_layer.get', workspace=workspace, layername=layername))
        resp_json = response.get_json()
        assert response.status_code == 400, resp_json
        assert resp_json['code'] == 2
        assert resp_json['detail']['parameter'] == 'layername'


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_get_layers_testuser1_v1(client):
    workspace = 'test_get_layers_testuser1_v1_user'
    layername = 'layer1'
    # publish and delete layer to ensure that username exists
    flask_client.publish_layer(workspace, layername, client)
    flask_client.delete_layer(workspace, layername, client)
    response = client.get(url_for('rest_workspace_layers.get', workspace=workspace))
    assert response.status_code == 200, response.get_json()
    # assert len(resp_json) == 0
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('ensure_layman')
def test_post_layers_simple(client):
    with app.app_context():
        workspace = 'testuser1'

        rest_path = url_for('rest_workspace_layers.post', workspace=workspace)
        file_paths = [
            'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
        ]
        for file_path in file_paths:
            assert os.path.isfile(file_path)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.post(rest_path, data={
                'file': files,
            })
        assert response.status_code == 200

        layername = 'ne_110m_admin_0_countries'

        chain_info = util.get_layer_chain(workspace, layername)
        assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
        layer_info = util.get_layer_info(workspace, layername)
        keys_to_check = ['db', 'wms', 'wfs', 'thumbnail', 'metadata']
        for key_to_check in keys_to_check:
            assert 'status' in layer_info[key_to_check]

        # For some reason this hangs forever on get() if run (either with src/layman/authz/read_everyone_write_owner_auth2_test.py::test_authn_map_access_rights or src/layman/authn/oauth2_test.py::test_patch_current_user_without_username) and with src/layman/common/metadata/util.csw_insert
        # last_task['last'].get()
        # e.g. python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/authn/oauth2_test.py::test_patch_current_user_without_username src/layman/layer/rest_workspace_test.py::test_post_layers_simple
        # this can badly affect also .get(propagate=False) in layman.celery.abort_task_chain
        # but hopefully this is only related to magic flask&celery test suite
        flask_client.wait_till_layer_ready(workspace, layername)

        layer_info = util.get_layer_info(workspace, layername)
        for key_to_check in keys_to_check:
            assert isinstance(layer_info[key_to_check], str) \
                or 'status' not in layer_info[key_to_check]

        layeruuid = layer_info['uuid']
        wms_layername = names.get_layer_names_by_source(uuid=layeruuid).wms
        wms_url = geoserver_wms.get_wms_url()
        wms = wms_proxy(wms_url)
        assert wms_layername.name in wms.contents

        assert settings.LAYMAN_REDIS.sismember(uuid.UUID_SET_KEY, layeruuid)
        assert settings.LAYMAN_REDIS.exists(uuid.get_uuid_metadata_key(layeruuid))
        assert settings.LAYMAN_REDIS.hexists(
            uuid.get_workspace_type_names_key(workspace, '.'.join(__name__.split('.')[:-1])),
            layername
        )

        layer_info = client.get(url_for('rest_workspace_layer.get', workspace=workspace, layername=layername)).get_json()
        assert set(layer_info['metadata'].keys()) == {'identifier', 'csw_url', 'record_url', 'comparison_url'}
        assert layer_info['metadata']['identifier'] == f"m-{layeruuid}"
        assert layer_info['metadata']['csw_url'] == settings.CSW_PROXY_URL
        md_record_url = f"http://micka:80/record/basic/m-{layeruuid}"
        assert layer_info['metadata']['record_url'].replace("http://localhost:3080", "http://micka:80") == md_record_url
        assert layer_info['metadata']['comparison_url'] == url_for_external('rest_workspace_layer_metadata_comparison.get',
                                                                            workspace=workspace, layername=layername)
        assert 'id' not in layer_info.keys()
        assert 'type' not in layer_info.keys()

        response = requests.get(md_record_url, auth=settings.CSW_BASIC_AUTHN,
                                timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        response.raise_for_status()
        assert layername in response.text

        publication_counter.increase()
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })

    with app.app_context():
        expected_md_values = {
            'abstract': None,
            'extent': [-180.0, -85.60903859383285, 180.0, 83.64513109859944],
            'graphic_url': url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                'identifier': url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                'label': 'ne_110m_admin_0_countries'
            },
            'language': ['eng'],
            'layer_endpoint': url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': None,
            'spatial_resolution': {
                'scale_denominator': 100000000,
            },
            'title': 'ne_110m_admin_0_countries',
        }
    check_metadata(client, workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('app_context')
def test_post_layers_concurrent(client):
    workspace = 'testuser1'
    layername = 'countries_concurrent'
    rest_path = url_for('rest_workspace_layers.post', workspace=workspace)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]
    for file_path in file_paths:
        assert os.path.isfile(file_path)
    with ExitStack() as stack:
        files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
        response = client.post(rest_path, data={
            'file': files,
            'name': layername,
        })
    assert response.status_code == 200

    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)

    with ExitStack() as stack:
        files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
        response = client.post(rest_path, data={
            'file': files,
            'name': layername,
        })
    assert response.status_code == 409
    resp_json = response.get_json()
    assert resp_json['code'] == 17

    publication_counter.increase()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_post_layers_shp_missing_extensions(client):
    workspace = 'testuser1'
    rest_path = url_for('rest_workspace_layers.post', workspace=workspace)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.dbf',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.VERSION.txt',
    ]
    for file_path in file_paths:
        assert os.path.isfile(file_path)
    with ExitStack() as stack:
        files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
        response = client.post(rest_path, data={
            'file': files,
            'name': 'ne_110m_admin_0_countries_shp',
        })
    resp_json = response.get_json()
    # print(resp_json)
    assert response.status_code == 400
    assert resp_json['code'] == 18
    assert sorted(resp_json['detail']['missing_extensions']) == [
        '.prj', '.shx']

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_post_layers_shp(client):
    workspace = 'testuser1'
    layername = 'ne_110m_admin_0_countries_shp'
    rest_path = url_for('rest_workspace_layers.post', workspace=workspace)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.cpg',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.dbf',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.prj',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.README.html',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shx',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.VERSION.txt',
    ]
    for file_path in file_paths:
        assert os.path.isfile(file_path)
    with ExitStack() as stack:
        files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
        response = client.post(rest_path, data={
            'file': files,
            'name': layername,
        })
    assert response.status_code == 200
    layeruuid = response.json[0]['uuid']

    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
    flask_client.wait_till_layer_ready(workspace, layername)
    # last_task['last'].get()

    wms_layername = names.get_layer_names_by_source(uuid=layeruuid).wms
    wms_url = geoserver_wms.get_wms_url()
    wms = wms_proxy(wms_url)
    assert wms_layername.name in wms.contents

    publication_counter.increase()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_post_layers_layer_exists(client):
    workspace = 'testuser1'
    rest_path = url_for('rest_workspace_layers.post', workspace=workspace)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]
    for file_path in file_paths:
        assert os.path.isfile(file_path)
    with ExitStack() as stack:
        files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
        response = client.post(rest_path, data={
            'file': files,
        })
    assert response.status_code == 409
    resp_json = response.get_json()
    assert resp_json['code'] == 17

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('ensure_layman')
def test_post_layers_complex(client):
    with app.app_context():
        workspace = 'testuser2'
        rest_path = url_for('rest_workspace_layers.post', workspace=workspace)
        file_paths = [
            'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
        ]
        for file_path in file_paths:
            assert os.path.isfile(file_path)
        sld_path = 'sample/style/generic-blue_sld.xml'
        assert os.path.isfile(sld_path)
        layername = ''
        with ExitStack() as stack, open(sld_path, 'rb') as sld_file:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.post(rest_path, data={
                'file': files,
                'name': 'countries',
                'title': 'staty',
                'description': 'popis států',
                'style': (sld_file, os.path.basename(sld_path)),
            })
        assert response.status_code == 200
        resp_json = response.get_json()
        # print(resp_json)
        layername = resp_json[0]['name']
        layeruuid = resp_json[0]['uuid']

        chain_info = util.get_layer_chain(workspace, layername)
        assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
        flask_client.wait_till_layer_ready(workspace, layername)
        # last_task['last'].get()
        assert celery_util.is_chain_ready(chain_info)

        all_names = names.get_layer_names_by_source(uuid=layeruuid)
        wms_layername = all_names.wms
        wms_url = geoserver_wms.get_wms_url()
        wms = wms_proxy(wms_url)
        assert wms_layername.name in wms.contents
        assert wms[wms_layername.name].title == 'staty'
        assert wms[wms_layername.name].abstract == 'popis států'
        assert wms[wms_layername.name].styles[all_names.sld.name]['title'] == 'Generic Blue'

        assert layername != ''
        rest_path = url_for('rest_workspace_layer.get', workspace=workspace, layername=layername)
        response = client.get(rest_path)
        assert 200 <= response.status_code < 300
        resp_json = response.get_json()
        # print(resp_json)
        assert resp_json['title'] == 'staty'
        assert resp_json['description'] == 'popis států'
        for source in [
            'wms',
            'wfs',
            'thumbnail',
            'file',
            'db',
            'metadata',
        ]:
            assert 'status' not in resp_json[source]

        style_url = geoserver_sld.get_workspace_style_url(uuid=layeruuid)
        response = requests.get(style_url + '.sld',
                                auth=settings.LAYMAN_GS_AUTH,
                                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                                )
        response.raise_for_status()
        sld_file = io.BytesIO(response.content)
        tree = ET.parse(sld_file)
        root = tree.getroot()
        assert root.attrib['version'] == '1.0.0'

        db_store = DEFAULT_INTERNAL_DB_STORE
        feature_type = get_feature_type(all_names.wfs.workspace, db_store, all_names.wfs.name)
        attributes = feature_type['attributes']['attribute']
        assert next((
            a for a in attributes if a['name'] == 'sovereignt'
        ), None) is not None

        publication_counter.increase()
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })

    with app.app_context():
        expected_md_values = {
            'abstract': "popis st\u00e1t\u016f",
            'extent': [-180.0, -85.60903859383285, 180.0, 83.64513109859944],
            'graphic_url': url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                "identifier": url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                "label": "countries"
            },
            'language': ["eng"],
            'layer_endpoint': url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': None,
            'spatial_resolution': {
                'scale_denominator': 100000000,
            },
            'title': "staty",
        }
    check_metadata(client, workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('ensure_layman')
def test_uppercase_attr(client):
    with app.app_context():
        workspace = 'testuser2'
        rest_path = url_for('rest_workspace_layers.post', workspace=workspace)
        file_paths = [
            'sample/data/upper_attr.geojson',
        ]
        for file_path in file_paths:
            assert os.path.isfile(file_path)
        files = []
        sld_path = 'sample/data/upper_attr.sld'
        assert os.path.isfile(sld_path)
        layername = 'upper_attr'
        publ_uuid = '18007abf-e7e8-4895-9c87-1a646a8771fe'
        with ExitStack() as stack, open(sld_path, 'rb') as sld_file:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.post(rest_path, data={
                'file': files,
                'name': layername,
                'style': (sld_file, os.path.basename(sld_path)),
                'uuid': publ_uuid,
            })
        assert response.status_code == 200
        resp_json = response.get_json()
        # print(resp_json)

        chain_info = util.get_layer_chain(workspace, layername)
        assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
        flask_client.wait_till_layer_ready(workspace, layername)
        # last_task['last'].get()
        assert celery_util.is_chain_ready(chain_info)

    with app.app_context():
        rest_path = url_for('rest_workspace_layer.get', workspace=workspace, layername=layername)
        response = client.get(rest_path)
        assert 200 <= response.status_code < 300
        resp_json = response.get_json()
        # print(resp_json)
        for source in [
            'wms',
            'wfs',
            'thumbnail',
            'file',
            'db',
            'metadata',
        ]:
            assert 'status' not in resp_json[source], f"{source}: {resp_json[source]}"

        layeruuid = resp_json['uuid']
        gs_layername = names.get_layer_names_by_source(uuid=layeruuid, ).wfs
        db_store = DEFAULT_INTERNAL_DB_STORE
        feature_type = get_feature_type(gs_layername.workspace, db_store, gs_layername.name)
        attributes = feature_type['attributes']['attribute']
        attr_names = ["id", "dpr_smer_k", "fid_zbg", "silnice", "silnice_bs", "typsil_p", "cislouseku", "jmeno",
                      "typsil_k", "peazkom1", "peazkom2", "peazkom3", "peazkom4", "vym_tahy_k", "vym_tahy_p",
                      "r_indsil7", "kruh_obj_k", "etah1", "etah2", "etah3", "etah4", "kruh_obj_p", "dpr_smer_p"]
        for attr_name in attr_names:
            assert next((
                a for a in attributes if a['name'] == attr_name
            ), None) is not None

        th_path = get_layer_thumbnail_path(publ_uuid)
        assert os.path.getsize(th_path) > 5000

    with app.app_context():
        rest_path = url_for('rest_workspace_layer.delete_layer', workspace=workspace, layername=layername)
        response = client.delete(rest_path)
        assert 200 <= response.status_code < 300

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_get_layers_testuser1_v2(client):
    workspace = 'testuser1'
    layer1 = 'countries_concurrent'
    layer2 = 'ne_110m_admin_0_countries'
    layer3 = 'ne_110m_admin_0_countries_shp'
    response = client.get(url_for('rest_workspace_layers.get', workspace=workspace))
    assert response.status_code == 200
    resp_json = response.get_json()
    # assert len(resp_json) == 3
    layernames = [layer['name'] for layer in resp_json]
    for layer in [
        layer1,
        layer2,
        layer3,
    ]:
        assert layer in layernames

    workspace = 'testuser2'
    response = client.get(url_for('rest_workspace_layers.get', workspace=workspace))
    resp_json = response.get_json()
    assert response.status_code == 200
    assert len(resp_json) == 1
    assert resp_json[0]['name'] == 'countries'

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('ensure_layman')
def test_patch_layer_title(client):
    with app.app_context():
        workspace = 'testuser1'
        layername = 'ne_110m_admin_0_countries'
        rest_path = url_for('rest_workspace_layer.patch', workspace=workspace, layername=layername)
        new_title = "New Title of Countries"
        new_description = "and new description"
        response = client.patch(rest_path, data={
            'title': new_title,
            'description': new_description,
        })
        assert response.status_code == 200, response.get_json()

        flask_client.wait_till_layer_ready(workspace, layername)
        chain_info = util.get_layer_chain(workspace, layername)
        assert chain_info is not None and celery_util.is_chain_ready(chain_info)

        get_json = client.get(rest_path).get_json()
        assert get_json['title'] == new_title
        assert get_json['description'] == new_description

    with app.app_context():
        expected_md_values = {
            'abstract': "and new description",
            'extent': [-180.0, -85.60903859383285, 180.0, 83.64513109859944],
            'graphic_url': url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                'identifier': url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                'label': 'ne_110m_admin_0_countries'
            },
            'language': ['eng'],
            'layer_endpoint': url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': TODAY_DATE,
            'spatial_resolution': {
                'scale_denominator': 100000000,
            },
            'title': "New Title of Countries",
        }
        check_metadata(client, workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })


@pytest.mark.usefixtures('ensure_layman')
def test_patch_layer_style(client):
    with app.app_context():
        workspace = 'testuser1'
        layername = 'ne_110m_admin_0_countries'
        rest_path = url_for('rest_workspace_layer.patch', workspace=workspace, layername=layername)
        sld_path = 'sample/style/generic-blue_sld.xml'
        assert os.path.isfile(sld_path)
        with open(sld_path, 'rb') as sld_file:
            response = client.patch(rest_path, data={
                'style': (sld_file, os.path.basename(sld_path)),
                'title': 'countries in blue'
            })
        assert response.status_code == 200
        layeruuid = response.json['uuid']

        # last_task = util._get_layer_task(workspace, layername)

        # Time to generate testing thumbnail is probably shorter than getting & parsing WMS/WFS capabilities documents
        # so it's finished before PATCH request is completed
        #
        # assert last_task is not None and not util._is_task_ready(last_task)
        # resp_json = rv.get_json()
        # keys_to_check = ['thumbnail']
        # for key_to_check in keys_to_check:
        #         assert 'status' in resp_json[key_to_check]
        flask_client.wait_till_layer_ready(workspace, layername)
        # last_task['last'].get()

        get_json = client.get(rest_path).get_json()
        assert get_json['title'] == "countries in blue"

        all_names = names.get_layer_names_by_source(uuid=layeruuid)
        wms_layername = all_names.wms
        wms_url = geoserver_wms.get_wms_url()
        wms = wms_proxy(wms_url)
        assert wms_layername.name in wms.contents
        assert wms[wms_layername.name].title == 'countries in blue'
        assert wms[wms_layername.name].styles[all_names.sld.name]['title'] == 'Generic Blue'

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })

        expected_md_values = {
            'abstract': "and new description",
            'extent': [-180.0, -85.60903859383285, 180.0, 83.64513109859944],
            'graphic_url': url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                'identifier': url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                'label': 'ne_110m_admin_0_countries'
            },
            'language': ['eng'],
            'layer_endpoint': url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': TODAY_DATE,
            'spatial_resolution': {
                'scale_denominator': 100000000,
            },
            'title': 'countries in blue',
        }
    check_metadata(client, workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('ensure_layman')
def test_patch_layer_data(client):
    with app.app_context():
        workspace = 'testuser2'
        layername = 'countries'
        rest_path = url_for('rest_workspace_layer.patch', workspace=workspace, layername=layername)
        file_paths = [
            'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson',
        ]
        for file_path in file_paths:
            assert os.path.isfile(file_path)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.patch(rest_path, data={
                'file': files,
                'title': 'populated places'
            })
        assert response.status_code == 200

        chain_info = util.get_layer_chain(workspace, layername)
        assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
        get_json = client.get(rest_path).get_json()
        keys_to_check = ['db', 'wms', 'wfs', 'thumbnail', 'metadata']
        for key_to_check in keys_to_check:
            assert 'status' in get_json[key_to_check]
        flask_client.wait_till_layer_ready(workspace, layername)
        layeruuid = get_json['uuid']
        # last_task['last'].get()

    with app.app_context():
        rest_path = url_for('rest_workspace_layer.get', workspace=workspace, layername=layername)
        response = client.get(rest_path)
        assert 200 <= response.status_code < 300

        resp_json = response.get_json()
        assert resp_json['title'] == "populated places"
        gs_layername = names.get_layer_names_by_source(uuid=layeruuid, ).wfs
        db_store = DEFAULT_INTERNAL_DB_STORE
        feature_type = get_feature_type(gs_layername.workspace, db_store, gs_layername.name)
        attributes = feature_type['attributes']['attribute']
        assert next((
            a for a in attributes if a['name'] == 'sovereignt'
        ), None) is None
        assert next((
            a for a in attributes if a['name'] == 'adm0cap'
        ), None) is not None

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })

    with app.app_context():
        expected_md_values = {
            'abstract': "popis st\u00e1t\u016f",
            'extent': [-175.22056435043098, -41.29999116752133, 179.21664802661394, 64.15002486626597],
            'graphic_url': url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                'identifier': url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                "label": "countries"
            },
            'language': ["eng", 'chi', 'rus'],
            'layer_endpoint': url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': TODAY_DATE,
            'spatial_resolution': None,  # it's point data now and we can't guess scale from point data
            'title': 'populated places',
        }
    check_metadata(client, workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('ensure_layman')
def test_patch_layer_concurrent_and_delete_it(client):
    with app.app_context():
        workspace = 'testuser2'
        layername = 'countries'
        rest_path = url_for('rest_workspace_layer.patch', workspace=workspace, layername=layername)
        file_paths = [
            'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
        ]
        for file_path in file_paths:
            assert os.path.isfile(file_path)

        uuid_str = get_publication_uuid(workspace, LAYER_TYPE, layername)

        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.patch(rest_path, data={
                'file': files,
                'title': 'populated places'
            })
        assert response.status_code == 200

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })

        chain_info = util.get_layer_chain(workspace, layername)
        assert chain_info is not None and not celery_util.is_chain_ready(chain_info)

    with app.app_context():
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.patch(rest_path, data={
                'file': files,
            })
        assert response.status_code == 400, response.get_json()
        resp_json = response.get_json()
        assert resp_json['code'] == 49

        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })

    with app.app_context():
        rest_path = url_for('rest_workspace_layer.delete_layer', workspace=workspace, layername=layername)
        response = client.delete(rest_path)
        assert response.status_code == 200

        assert not settings.LAYMAN_REDIS.sismember(uuid.UUID_SET_KEY, uuid_str)
        assert not settings.LAYMAN_REDIS.exists(uuid.get_uuid_metadata_key(uuid_str))
        assert not settings.LAYMAN_REDIS.hexists(
            uuid.get_workspace_type_names_key(workspace, '.'.join(__name__.split('.')[:-1])),
            layername
        )

        publication_counter.decrease()
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_post_layers_long_and_delete_it(client):
    workspace = 'testuser1'
    rest_path = url_for('rest_workspace_layers.post', workspace=workspace)
    file_paths = [
        'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
    ]
    for file_path in file_paths:
        assert os.path.isfile(file_path)
    with ExitStack() as stack:
        files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
        response = client.post(rest_path, data={
            'file': files,
        })
    assert response.status_code == 200

    layername = 'ne_10m_admin_0_countries'

    time.sleep(1)

    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
    layer_info = util.get_complete_layer_info(workspace, layername)

    # sometimes, "long" post is not long enough and the layer is already in COMPLETE state
    if layer_info['layman_metadata']['publication_status'] == 'UPDATING':
        keys_to_check = ['db', 'wms', 'wfs', 'thumbnail', 'metadata']
        for key_to_check in keys_to_check:
            assert 'status' in layer_info[key_to_check]

    rest_path = url_for('rest_workspace_layer.delete_layer', workspace=workspace, layername=layername)
    response = client.delete(rest_path)
    assert response.status_code == 200
    response = client.get(url_for('rest_workspace_layer.get', workspace=workspace, layername=layername))
    # print(resp_json)
    assert response.status_code == 404

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_delete_layer(client):
    workspace = 'testuser1'
    layername = 'ne_110m_admin_0_countries'
    rest_path = url_for('rest_workspace_layer.delete_layer', workspace=workspace, layername=layername)
    response = client.delete(rest_path)
    assert response.status_code == 200

    publication_counter.decrease()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })

    rest_path = url_for('rest_workspace_layer.delete_layer', workspace=workspace, layername=layername)
    response = client.delete(rest_path)
    assert response.status_code == 404
    resp_json = response.get_json()
    assert resp_json['code'] == 15


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_post_layers_zero_length_attribute():
    workspace = 'testuser1'
    layername = 'zero_length_attribute'
    file_paths = [
        'sample/data/zero_length_attribute.geojson',
    ]

    def wait_for_db_finish(response):
        info = response.json()
        return info.get('db', {}).get('status', '') == 'FAILURE'

    process_client.publish_workspace_layer(workspace, layername, file_paths=file_paths,
                                           check_response_fn=wait_for_db_finish, raise_if_not_complete=False)

    layer_info = util.get_layer_info(workspace, layername)
    assert layer_info['db']['status'] == 'FAILURE', f'layer_info={layer_info}'
    assert layer_info['db']['error']['code'] == 28, f'layer_info={layer_info}'

    process_client.delete_workspace_layer(workspace, layername)

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('app_context', 'ensure_layman')
def test_get_layers_testuser2(client):
    workspace = 'testuser2'
    response = client.get(url_for('rest_workspace_layers.get', workspace=workspace))
    assert response.status_code == 200
    resp_json = response.get_json()
    assert len(resp_json) == 0

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


@pytest.mark.usefixtures('ensure_layman')
def test_just_delete_layers(client):
    flask_client.delete_layer('testuser1', 'countries_concurrent', client)
    flask_client.delete_layer('testuser1', 'ne_110m_admin_0_countries_shp', client)


@pytest.mark.usefixtures('ensure_layman')
def test_layer_with_different_geometry():
    workspace = 'testgeometryuser1'
    layername = 'layer_with_different_geometry'
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson',
    ]
    response = process_client.publish_workspace_layer(workspace, layername, file_paths=file_paths)
    layeruuid = response['uuid']

    url_path_ows = urljoin(urljoin(settings.LAYMAN_GS_URL, workspace), 'ows?service=WFS&request=Transaction')
    url_path_wfs = urljoin(urljoin(settings.LAYMAN_GS_URL, workspace), 'wfs?request=Transaction')

    headers_wfs = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    gs_layername = names.get_layer_names_by_source(uuid=layeruuid, ).wfs
    data_xml = data_wfs.get_wfs20_insert_points(gs_layername.workspace, gs_layername.name)

    response = requests.post(url_path_ows,
                             data=data_xml,
                             headers=headers_wfs,
                             auth=settings.LAYMAN_GS_AUTH,
                             timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                             )
    response.raise_for_status()

    response = requests.post(url_path_wfs,
                             data=data_xml,
                             headers=headers_wfs,
                             auth=settings.LAYMAN_GS_AUTH,
                             timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                             )
    assert response.status_code == 200, f"HTTP Error {response.status_code}\n{response.text}"

    data_xml2 = data_wfs.get_wfs20_insert_lines(gs_layername.workspace, gs_layername.name)

    response = requests.post(url_path_ows,
                             data=data_xml2,
                             headers=headers_wfs,
                             auth=settings.LAYMAN_GS_AUTH,
                             timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                             )
    assert response.status_code == 200, f"HTTP Error {response.status_code}\n{response.text}"

    response = requests.post(url_path_wfs,
                             data=data_xml2,
                             headers=headers_wfs,
                             auth=settings.LAYMAN_GS_AUTH,
                             timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                             )
    assert response.status_code == 200, f"HTTP Error {response.status_code}\n{response.text}"
    process_client.delete_workspace_layer(workspace, layername)
