from datetime import date
import os
import json
import time
from urllib.parse import urljoin
import requests
import pytest

from geoserver.util import get_feature_type
from layman import app, uuid, LaymanError, settings, celery as celery_util
from layman.common import empty_method_returns_true
from layman.common.metadata import prop_equals_strict, PROPERTIES
from layman.layer.filesystem.thumbnail import get_layer_thumbnail_path
from layman.layer.geoserver import wms as geoserver_wms, GeoserverIds
from layman.util import SimpleCounter, get_publication_uuid
from test_tools import process_client, util as test_util
from test_tools.data import wfs as data_wfs
from . import util, LAYER_TYPE
from .geoserver.util import wms_proxy, DEFAULT_INTERNAL_DB_STORE


USER = 'testuser1'
WORKSPACE_2 = 'testuser2'
LAYERNAME_1 = 'countries_concurrent'
LAYERNAME_2 = 'ne_110m_admin_0_countries'
LAYERNAME_3 = 'ne_110m_admin_0_countries_shp'
LAYERNAME_4 = 'countries'

publication_counter = SimpleCounter()

TODAY_DATE = date.today().strftime('%Y-%m-%d')

EXP_REFERENCE_SYSTEMS = [3034, 3035, 3059, 3857, 4326, 5514, 32633, 32634, 9377, 32718, ]

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


def check_metadata(workspace, layername, props_equal, expected_values):
    with app.app_context():
        resp_json = process_client.get_workspace_layer_metadata_comparison(workspace=workspace, name=layername)
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


@pytest.fixture(scope="module", autouse=True)
# pylint: disable=unused-argument
def ensure_layman(ensure_layman_module):
    yield


@pytest.mark.parametrize('workspace', [
    (' ', ),
    ('ě', ),
    (';', ),
    ('?', ),
    ('ABC', ),
])
def test_wrong_value_of_workspace(workspace):
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_layer(workspace=workspace,
                                               name=None,
                                               )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 2
    assert exc_info.value.data['parameter'] == 'workspace'


def test_layman_gs_user_conflict():
    """Tests that Layman detects that reserved username is in conflict with LAYMAN_GS_USER.

    See https://github.com/LayerManager/layman/pull/97
    """

    workspace = settings.LAYMAN_GS_USER
    layername = 'layer1'
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_layer(workspace=workspace,
                                               name=layername,
                                               )
    assert exc_info.value.http_code == 409
    assert exc_info.value.code == 41


@pytest.mark.parametrize('layername', [
    (' ', ),
    ('ě', ),
    (';', ),
    ('?', ),
    ('ABC', ),
])
def test_wrong_value_of_layername(layername):
    workspace = 'test_wrong_value_of_layername_workspace'
    # publish and delete layer to ensure that username exists
    process_client.ensure_workspace(workspace)
    with pytest.raises(LaymanError) as exc_info:
        process_client.get_workspace_layer(workspace=workspace,
                                           name=layername,
                                           )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 2
    assert exc_info.value.data['parameter'] == 'layername'


def test_get_layers_testuser1_v1():
    workspace = 'test_get_layers_testuser1_v1_user'
    # publish and delete layer to ensure that username exists
    process_client.ensure_workspace(workspace)
    process_client.get_layers(workspace=workspace,
                              )
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_post_layers_simple():
    workspace = USER
    process_client.publish_workspace_layer(workspace=workspace,
                                           name=None,
                                           file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'],
                                           check_response_fn=empty_method_returns_true,
                                           raise_if_not_complete=False,
                                           do_not_post_name=True,
                                           )
    layername = LAYERNAME_2
    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
    with app.app_context():
        layer_info = util.get_layer_info(workspace, layername)
    # keys_to_check = ['db', 'wms', 'wfs', 'thumbnail', 'metadata']
    keys_to_check = ['wms', 'thumbnail', 'metadata']
    for key_to_check in keys_to_check:
        assert 'status' in layer_info[key_to_check], f'{key_to_check=}\n{layer_info=}'

    process_client.wait_for_publication_status(workspace=workspace, publication_type=LAYER_TYPE, publication=layername)

    with app.app_context():
        layer_info = util.get_layer_info(workspace, layername)
    for key_to_check in keys_to_check:
        assert isinstance(layer_info[key_to_check], str) \
            or 'status' not in layer_info[key_to_check]

    layeruuid = layer_info['uuid']
    wms_layername = GeoserverIds(uuid=layeruuid).wms
    wms_url = geoserver_wms.get_wms_url()
    wms = wms_proxy(wms_url)
    assert wms_layername.name in wms.contents

    assert settings.LAYMAN_REDIS.sismember(uuid.UUID_SET_KEY, layeruuid)
    assert settings.LAYMAN_REDIS.exists(uuid.get_uuid_metadata_key(layeruuid))
    assert settings.LAYMAN_REDIS.hexists(
        uuid.get_workspace_type_names_key(workspace, '.'.join(__name__.split('.')[:-1])),
        layername
    )

    layer_info = process_client.get_workspace_layer(workspace=workspace, name=layername)
    assert set(layer_info['metadata'].keys()) == {'identifier', 'csw_url', 'record_url', 'comparison_url'}
    assert layer_info['metadata']['identifier'] == f"m-{layeruuid}"
    assert layer_info['metadata']['csw_url'] == settings.CSW_PROXY_URL
    md_record_url = f"http://micka:80/record/basic/m-{layeruuid}"
    assert layer_info['metadata']['record_url'].replace("http://localhost:3080", "http://micka:80") == md_record_url
    with app.app_context():
        assert layer_info['metadata']['comparison_url'] == test_util.url_for_external('rest_workspace_layer_metadata_comparison.get',
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
            'graphic_url': test_util.url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                'identifier': test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                'label': 'ne_110m_admin_0_countries'
            },
            'language': ['eng'],
            'layer_endpoint': test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': None,
            'spatial_resolution': {
                'scale_denominator': 100000000,
            },
            'title': 'ne_110m_admin_0_countries',
        }
    check_metadata(workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)


def test_post_layers_concurrent():
    workspace = USER
    layername = LAYERNAME_1
    process_client.publish_workspace_layer(workspace=workspace,
                                           name=layername,
                                           file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'],
                                           check_response_fn=empty_method_returns_true,
                                           raise_if_not_complete=False,
                                           )
    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
    publication_counter.increase()

    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_layer(workspace=workspace,
                                               name=layername,
                                               file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'],
                                               )
    assert exc_info.value.http_code == 409
    assert exc_info.value.code == 17

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_post_layers_shp_missing_extensions():
    workspace = USER
    layername = LAYERNAME_3
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_layer(workspace=workspace,
                                               name=layername,
                                               file_paths=[
                                                   'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.dbf',
                                                   'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp',
                                                   'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.VERSION.txt',
                                               ],
                                               )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 18
    assert sorted(exc_info.value.data['missing_extensions']) == [
        '.prj', '.shx']

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_post_layers_shp():
    workspace = USER
    layername = LAYERNAME_3
    post_response = process_client.publish_workspace_layer(workspace=workspace,
                                                           name=layername,
                                                           file_paths=[
                                                               'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.cpg',
                                                               'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.dbf',
                                                               'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.prj',
                                                               'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.README.html',
                                                               'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp',
                                                               'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shx',
                                                               'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.VERSION.txt',
                                                           ],
                                                           check_response_fn=empty_method_returns_true,
                                                           raise_if_not_complete=False,
                                                           )
    layeruuid = post_response['uuid']
    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
    publication_counter.increase()
    process_client.wait_for_publication_status(workspace=workspace, publication_type=LAYER_TYPE, publication=layername)

    wms_layername = GeoserverIds(uuid=layeruuid).wms
    wms_url = geoserver_wms.get_wms_url()
    wms = wms_proxy(wms_url)
    assert wms_layername.name in wms.contents

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_post_layers_layer_exists():
    workspace = USER
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_layer(workspace=workspace,
                                               name=None,
                                               file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
                                                           ],
                                               )
    assert exc_info.value.http_code == 409
    assert exc_info.value.code == 17

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_post_layers_complex():
    workspace = WORKSPACE_2
    layername = LAYERNAME_4
    title = 'staty'
    description = 'popis států'
    post_response = process_client.publish_workspace_layer(workspace=workspace,
                                                           name=layername,
                                                           file_paths=[
                                                               'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
                                                           ],
                                                           title=title,
                                                           description=description,
                                                           style_file='sample/style/generic-blue_sld.xml',

                                                           check_response_fn=empty_method_returns_true,
                                                           raise_if_not_complete=False,
                                                           )
    layeruuid = post_response['uuid']
    assert post_response['name'] == layername

    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
    publication_counter.increase()
    process_client.wait_for_publication_status(workspace=workspace, publication_type=LAYER_TYPE, publication=layername)
    assert celery_util.is_chain_ready(chain_info)

    all_names = GeoserverIds(uuid=layeruuid)
    wms_layername = all_names.wms
    wms_url = geoserver_wms.get_wms_url()
    wms = wms_proxy(wms_url)
    assert wms_layername.name in wms.contents
    assert wms[wms_layername.name].title == 'staty'
    assert wms[wms_layername.name].abstract == 'popis států'
    assert wms[wms_layername.name].styles[all_names.sld.name]['title'] == 'Generic Blue'

    get_response = process_client.get_workspace_layer(workspace=workspace, name=layername)
    assert get_response['title'] == title
    assert get_response['description'] == description
    for source in [
        'wms',
        'wfs',
        'thumbnail',
        'file',
        'db',
        'metadata',
    ]:
        assert 'status' not in get_response[source]

    tree = process_client.get_workspace_layer_style(workspace=workspace, layer=layername)
    root = tree.getroot()
    assert root.attrib['version'] == '1.0.0'

    db_store = DEFAULT_INTERNAL_DB_STORE
    feature_type = get_feature_type(all_names.wfs.workspace, db_store, all_names.wfs.name)
    attributes = feature_type['attributes']['attribute']
    assert next((
        a for a in attributes if a['name'] == 'sovereignt'
    ), None) is not None

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })

    with app.app_context():
        expected_md_values = {
            'abstract': "popis st\u00e1t\u016f",
            'extent': [-180.0, -85.60903859383285, 180.0, 83.64513109859944],
            'graphic_url': test_util.url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                "identifier": test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                "label": "countries"
            },
            'language': ["eng"],
            'layer_endpoint': test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': None,
            'spatial_resolution': {
                'scale_denominator': 100000000,
            },
            'title': "staty",
        }
    check_metadata(workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)


def test_uppercase_attr():
    workspace = WORKSPACE_2
    layername = 'upper_attr'
    publ_uuid = '18007abf-e7e8-4895-9c87-1a646a8771fe'
    process_client.publish_workspace_layer(workspace=workspace,
                                           name=layername,
                                           file_paths=[
                                               'sample/data/upper_attr.geojson',
                                           ],
                                           style_file='sample/data/upper_attr.sld',
                                           uuid=publ_uuid,
                                           check_response_fn=empty_method_returns_true,
                                           raise_if_not_complete=False,
                                           )

    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
    publication_counter.increase()
    process_client.wait_for_publication_status(workspace=workspace, publication_type=LAYER_TYPE, publication=layername)
    assert celery_util.is_chain_ready(chain_info)

    get_response = process_client.get_workspace_layer(workspace=workspace, name=layername)
    for source in [
        'wms',
        'wfs',
        'thumbnail',
        'file',
        'db',
        'metadata',
    ]:
        assert 'status' not in get_response[source]

    layeruuid = get_response['uuid']
    gs_layername = GeoserverIds(uuid=layeruuid, ).wfs
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

    with app.app_context():
        th_path = get_layer_thumbnail_path(publ_uuid)
    assert os.path.getsize(th_path) > 5000

    process_client.delete_workspace_layer(workspace=workspace, name=layername)
    publication_counter.decrease()

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_get_layers_testuser1_v2():
    workspace = USER
    layername_1 = LAYERNAME_1
    layername_2 = LAYERNAME_2
    layername_3 = LAYERNAME_3
    layername_4 = LAYERNAME_4

    gets_response = process_client.get_layers(workspace=workspace)
    layernames = [layer['name'] for layer in gets_response]
    for layer in [
        layername_1,
        layername_2,
        layername_3,
    ]:
        assert layer in layernames

    workspace_2 = WORKSPACE_2
    gets_response_2 = process_client.get_layers(workspace=workspace_2)
    assert len(gets_response_2) == 1
    assert gets_response_2[0]['name'] == layername_4

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_patch_layer_title():
    workspace = USER
    layername = LAYERNAME_2
    new_title = "New Title of Countries"
    new_description = "and new description"

    process_client.patch_workspace_layer(workspace, layername,
                                         title=new_title,
                                         description=new_description,
                                         )
    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and celery_util.is_chain_ready(chain_info)

    get_response = process_client.get_workspace_layer(workspace=workspace, name=layername)
    assert get_response['title'] == new_title
    assert get_response['description'] == new_description

    with app.app_context():
        expected_md_values = {
            'abstract': "and new description",
            'extent': [-180.0, -85.60903859383285, 180.0, 83.64513109859944],
            'graphic_url': test_util.url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                'identifier': test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                'label': 'ne_110m_admin_0_countries'
            },
            'language': ['eng'],
            'layer_endpoint': test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': TODAY_DATE,
            'spatial_resolution': {
                'scale_denominator': 100000000,
            },
            'title': "New Title of Countries",
        }
    check_metadata(workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_patch_layer_style():
    workspace = USER
    layername = LAYERNAME_2
    new_title = 'countries in blue'

    sld_path = 'sample/style/generic-blue_sld.xml'
    process_client.patch_workspace_layer(workspace, layername,
                                         title=new_title,
                                         style_file=sld_path,
                                         )

    get_response = process_client.get_workspace_layer(workspace=workspace, name=layername)
    assert get_response['title'] == new_title
    layer_uuid = get_response['uuid']

    all_names = GeoserverIds(uuid=layer_uuid)
    wms_layername = all_names.wms
    wms_url = geoserver_wms.get_wms_url()
    wms = wms_proxy(wms_url)
    assert wms_layername.name in wms.contents
    assert wms[wms_layername.name].title == new_title
    assert wms[wms_layername.name].styles[all_names.sld.name]['title'] == 'Generic Blue'

    with app.app_context():
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': publication_counter.get()
        })

        expected_md_values = {
            'abstract': "and new description",
            'extent': [-180.0, -85.60903859383285, 180.0, 83.64513109859944],
            'graphic_url': test_util.url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                'identifier': test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                'label': 'ne_110m_admin_0_countries'
            },
            'language': ['eng'],
            'layer_endpoint': test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': TODAY_DATE,
            'spatial_resolution': {
                'scale_denominator': 100000000,
            },
            'title': 'countries in blue',
        }
    check_metadata(workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)


def test_patch_layer_data():
    workspace = WORKSPACE_2
    layername = LAYERNAME_4
    new_title = 'populated places'
    process_client.patch_workspace_layer(workspace, layername,
                                         file_paths=['tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson'],
                                         title=new_title,
                                         check_response_fn=empty_method_returns_true,
                                         raise_if_not_complete=False,
                                         )

    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
    get_incomplete_response = process_client.get_workspace_layer(workspace=workspace, name=layername)
    # keys_to_check = ['db', 'wms', 'wfs', 'thumbnail', 'metadata']
    keys_to_check = ['wms', 'thumbnail', 'metadata']
    for key_to_check in keys_to_check:
        assert 'status' in get_incomplete_response[key_to_check], f'{key_to_check=}\n{get_incomplete_response=}'
    process_client.wait_for_publication_status(workspace, LAYER_TYPE, layername)
    layer_uuid = get_incomplete_response['uuid']

    get_response = process_client.get_workspace_layer(workspace=workspace, name=layername)
    assert get_response['title'] == new_title
    gs_layername = GeoserverIds(uuid=layer_uuid, ).wfs
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
            'graphic_url': test_util.url_for_external('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
            'identifier': {
                'identifier': test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
                "label": "countries"
            },
            'language': ["eng", 'chi', 'rus'],
            'layer_endpoint': test_util.url_for_external('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': EXP_REFERENCE_SYSTEMS,
            'revision_date': TODAY_DATE,
            'spatial_resolution': None,  # it's point data now and we can't guess scale from point data
            'title': 'populated places',
        }
    check_metadata(workspace, layername, METADATA_PROPERTIES_EQUAL, expected_md_values)


def test_patch_layer_concurrent_and_delete_it():
    workspace = WORKSPACE_2
    layername = LAYERNAME_4
    new_title = 'populated places'

    with app.app_context():
        uuid_str = get_publication_uuid(workspace, LAYER_TYPE, layername)

    process_client.patch_workspace_layer(workspace, layername,
                                         file_paths=['tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson'],
                                         title=new_title,
                                         check_response_fn=empty_method_returns_true,
                                         raise_if_not_complete=False,
                                         )
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })
    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)

    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_layer(workspace, layername,
                                             file_paths=['tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson'],
                                             )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 49
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })

    process_client.delete_workspace_layer(workspace, layername)
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


def test_post_layers_long_and_delete_it():
    workspace = USER
    layername = 'ne_10m_admin_0_countries'

    post_response = process_client.publish_workspace_layer(
        workspace,
        name=None,
        file_paths=['tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson'],
        do_not_post_name=True,
        check_response_fn=empty_method_returns_true,
        raise_if_not_complete=False,
    )
    assert post_response['name'] == layername

    time.sleep(1)

    chain_info = util.get_layer_chain(workspace, layername)
    assert chain_info is not None and not celery_util.is_chain_ready(chain_info)
    with app.app_context():
        layer_info = util.get_complete_layer_info(workspace, layername)

    # sometimes, "long" post is not long enough and the layer is already in COMPLETE state
    if layer_info['layman_metadata']['publication_status'] == 'UPDATING':
        # keys_to_check = ['db', 'wms', 'wfs', 'thumbnail', 'metadata']
        keys_to_check = ['thumbnail', 'metadata']
        for key_to_check in keys_to_check:
            assert 'status' in layer_info[key_to_check], f'{key_to_check=}\n{layer_info=}'

    process_client.delete_workspace_layer(workspace, layername)

    with pytest.raises(LaymanError) as exc_info:
        process_client.get_workspace_layer(workspace, layername)
    assert exc_info.value.http_code == 404

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_delete_layer():
    workspace = USER
    layername = LAYERNAME_2

    process_client.delete_workspace_layer(workspace, layername)
    publication_counter.decrease()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })

    with pytest.raises(LaymanError) as exc_info:
        process_client.delete_workspace_layer(workspace, layername)
    assert exc_info.value.http_code == 404
    assert exc_info.value.code == 15

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_post_layers_zero_length_attribute():
    workspace = USER
    layername = 'zero_length_attribute'
    file_paths = [
        'sample/data/zero_length_attribute.geojson',
    ]

    def wait_for_db_finish(response):
        info = response.json()
        return info.get('db', {}).get('status', '') == 'FAILURE'

    process_client.publish_workspace_layer(workspace, layername, file_paths=file_paths,
                                           check_response_fn=wait_for_db_finish, raise_if_not_complete=False)

    with app.app_context():
        layer_info = util.get_layer_info(workspace, layername)
    assert layer_info['db']['status'] == 'FAILURE', f'layer_info={layer_info}'
    assert layer_info['db']['error']['code'] == 28, f'layer_info={layer_info}'

    process_client.delete_workspace_layer(workspace, layername)

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_get_layers_testuser2():
    workspace = WORKSPACE_2
    gets_response = process_client.get_layers(workspace=workspace)
    assert len(gets_response) == 0
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


def test_just_delete_layers():
    process_client.delete_workspace_layer(USER, LAYERNAME_1)
    publication_counter.decrease()
    process_client.delete_workspace_layer(USER, LAYERNAME_3)
    publication_counter.decrease()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': publication_counter.get()
    })


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

    gs_layername = GeoserverIds(uuid=layeruuid, ).wfs
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
