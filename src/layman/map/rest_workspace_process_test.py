from datetime import date
import json
import requests
import pytest

from layman import app, uuid, LaymanError, settings
from layman.common import empty_method_returns_true
from layman.common.metadata import prop_equals_strict, PROPERTIES
from layman.util import SimpleCounter, get_publication_uuid
from test_tools import process_client, util as test_util
from . import MAP_TYPE

TODAY_DATE = date.today().strftime('%Y-%m-%d')
USER = 'testuser1'
MAPNAME_1 = 'administrativni_cleneni_libereckeho_kraje'
MAPNAME_2 = 'libe'

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


def check_metadata(workspace, mapname, props_equal, expected_values):
    response = process_client.get_workspace_publication_metadata_comparison(
        process_client.MAP_TYPE,
        workspace, mapname,
    )
    assert METADATA_PROPERTIES == set(response['metadata_properties'].keys())
    for key, value in response['metadata_properties'].items():
        assert value['equal_or_null'] == (
            key in props_equal), f"Metadata property values have unexpected 'equal_or_null' value: {key}: {json.dumps(value, indent=2)}, sources: {json.dumps(response['metadata_sources'], indent=2)}"
        assert value['equal'] == (
            key in props_equal), f"Metadata property values have unexpected 'equal' value: {key}: {json.dumps(value, indent=2)}, sources: {json.dumps(response['metadata_sources'], indent=2)}"
        # print(f"'{k}': {json.dumps(list(v['values'].values())[0], indent=2)},")
        if key in expected_values:
            vals = list(value['values'].values())
            vals.append(expected_values[key])
            assert prop_equals_strict(vals, equals_fn=PROPERTIES[key].get('equals_fn',
                                                                          None)), \
                f"Property {key} has unexpected values {json.dumps(vals, indent=2)}"


@pytest.mark.usefixtures('ensure_layman_module')
def test_get_maps_empty():
    workspace = USER
    process_client.ensure_workspace(workspace)
    resp_json = process_client.get_maps(workspace=workspace)
    assert len(resp_json) == 0

    with app.app_context():
        uuid.check_redis_consistency(expected_publ_num_by_type={
            f'{MAP_TYPE}': publication_counter.get()
        })


@pytest.mark.parametrize('mapname', [
    (' ', ),
    ('ě', ),
    (';', ),
    ('?', ),
    ('ABC', ),
])
@pytest.mark.usefixtures('ensure_layman_module')
def test_wrong_value_of_mapname(mapname):
    workspace = USER
    with pytest.raises(LaymanError) as exc_info:
        process_client.get_workspace_map(workspace=workspace,
                                         name=mapname,
                                         )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 2
    assert exc_info.value.data['parameter'] == 'mapname'


@pytest.mark.usefixtures('ensure_layman_module')
def test_no_file():
    workspace = USER
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_map(workspace=workspace,
                                             name='map_without_file',
                                             file_paths=[],
                                             )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 1
    assert exc_info.value.data['parameter'] == 'file'


@pytest.mark.usefixtures('ensure_layman_module')
def test_post_maps_invalid_file():
    workspace = USER
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_map(workspace=workspace,
                                             name='map_invalid_file',
                                             file_paths=[
                                                 'sample/style/generic-blue_sld.xml',
                                             ],
                                             )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 2
    assert exc_info.value.data['parameter'] == 'file'
    assert exc_info.value.data['reason'] == 'Invalid JSON syntax'


@pytest.mark.usefixtures('ensure_layman_module')
def test_post_maps_invalid_json():
    workspace = USER
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_map(workspace=workspace,
                                             name='map_invalid_json',
                                             file_paths=[
                                                 'sample/layman.map/invalid-missing-title-email.json',
                                             ],
                                             )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 2
    assert exc_info.value.data['parameter'] == 'file'
    assert exc_info.value.data['reason'] == 'JSON not valid against schema https://raw.githubusercontent.com/hslayers/map-compositions/2.0.0/schema.json'
    assert len(exc_info.value.data['validation-errors']) == 2


@pytest.mark.usefixtures('ensure_layman_module')
def test_post_maps_simple():
    workspace = USER
    expected_mapname = MAPNAME_1
    post_resp = process_client.publish_workspace_map(workspace=workspace,
                                                     name=None,
                                                     file_paths=['sample/layman.map/full.json'],
                                                     check_response_fn=empty_method_returns_true,
                                                     raise_if_not_complete=False,
                                                     do_not_post_name=True,
                                                     )
    assert post_resp['name'] == expected_mapname
    mapname = post_resp['name']
    uuid_str = post_resp['uuid']
    assert uuid.is_valid_uuid(uuid_str)

    publication_counter.increase()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': publication_counter.get()
    })

    incomplete_get_resp = process_client.get_workspace_map(workspace=workspace,
                                                           name=mapname,
                                                           )
    assert incomplete_get_resp['name'] == mapname
    assert incomplete_get_resp['uuid'] == uuid_str
    with app.app_context():
        assert incomplete_get_resp['url'] == test_util.url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname)
    assert incomplete_get_resp['title'] == "Administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
    assert incomplete_get_resp[
        'description'] == "Na tematick\u00e9 map\u011b p\u0159i p\u0159ibl\u00ed\u017een\u00ed jsou postupn\u011b zobrazovan\u00e9 administrativn\u00ed celky Libereck\u00e9ho kraje : okresy, OP\u00da, ORP a obce."
    map_file = incomplete_get_resp['file']
    assert 'status' not in map_file
    assert 'path' in map_file
    with app.app_context():
        assert map_file['url'] == test_util.url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname)
    thumbnail = incomplete_get_resp['thumbnail']
    assert 'status' in thumbnail
    assert thumbnail['status'] in ['PENDING', 'STARTED']
    assert 'id' not in incomplete_get_resp.keys()
    assert 'type' not in incomplete_get_resp.keys()

    process_client.wait_for_publication_status(workspace, process_client.MAP_TYPE, mapname,
                                               check_response_fn=lambda response: not (
                                                   'status' in response.json()['thumbnail'] and response.json()['thumbnail']['status'] in [
                                                       'PENDING', 'STARTED']),
                                               raise_if_not_complete=False,
                                               sleeping_time=0.1,
                                               )

    after_thumbnail_get_resp = process_client.get_workspace_map(workspace=workspace,
                                                                name=mapname,
                                                                )
    thumbnail = after_thumbnail_get_resp['thumbnail']
    assert 'status' not in thumbnail
    assert 'path' in thumbnail
    with app.app_context():
        assert thumbnail['url'] == test_util.url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname)

    file_resp = process_client.get_workspace_map_file(process_client.MAP_TYPE, workspace, mapname)
    assert file_resp['name'] == mapname

    process_client.wait_for_publication_status(workspace, process_client.MAP_TYPE, mapname,
                                               check_response_fn=lambda response: not (
                                                   'status' in response.json()['metadata'] and response.json()['metadata']['status'] in [
                                                       'PENDING', 'STARTED']),
                                               raise_if_not_complete=False,
                                               sleeping_time=0.1,
                                               )

    after_metadata_get_resp = process_client.get_workspace_map(workspace=workspace,
                                                               name=mapname,
                                                               )

    assert set(after_metadata_get_resp['metadata'].keys()) == {'identifier', 'csw_url', 'record_url', 'comparison_url'}
    assert after_metadata_get_resp['metadata']['identifier'] == f"m-{uuid_str}"
    assert after_metadata_get_resp['metadata']['csw_url'] == settings.CSW_PROXY_URL
    md_record_url = f"http://micka:80/record/basic/m-{uuid_str}"
    assert after_metadata_get_resp['metadata']['record_url'].replace("http://localhost:3080", "http://micka:80") == md_record_url

    response = requests.get(md_record_url, auth=settings.CSW_BASIC_AUTHN, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    response.raise_for_status()
    assert mapname in response.text

    with app.app_context():
        expected_md_values = {
            'abstract': "Na tematick\u00e9 map\u011b p\u0159i p\u0159ibl\u00ed\u017een\u00ed jsou postupn\u011b zobrazovan\u00e9 administrativn\u00ed celky Libereck\u00e9ho kraje : okresy, OP\u00da, ORP a obce.",
            'extent': [
                14.62,
                50.58,
                15.42,
                50.82
            ],
            'graphic_url': test_util.url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname),
            'identifier': {
                "identifier": test_util.url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
                "label": mapname,
            },
            'map_endpoint': test_util.url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
            'map_file_endpoint': test_util.url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname),
            'operates_on': [],
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': [
                'EPSG:3857'
            ],
            'revision_date': None,
            'title': "Administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje",
        }
    check_metadata(workspace, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('ensure_layman_module')
@pytest.mark.timeout(60)
def test_post_maps_complex():
    workspace = USER
    mapname = MAPNAME_2
    title = 'Liberecký kraj: Administrativní členění'
    description = 'Libovolný popis'
    post_resp = process_client.publish_workspace_map(workspace=workspace,
                                                     name=mapname,
                                                     title=title,
                                                     description=description,
                                                     file_paths=['sample/layman.map/full.json'],
                                                     check_response_fn=empty_method_returns_true,
                                                     raise_if_not_complete=False,
                                                     )
    assert post_resp['name'] == mapname
    uuid_str = post_resp['uuid']
    assert uuid.is_valid_uuid(uuid_str)

    publication_counter.increase()
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': publication_counter.get()
    })

    incomplete_get_resp = process_client.get_workspace_map(workspace=workspace,
                                                           name=mapname,
                                                           )
    assert incomplete_get_resp['name'] == mapname
    assert incomplete_get_resp['uuid'] == uuid_str
    with app.app_context():
        assert incomplete_get_resp['url'] == test_util.url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname)
    assert incomplete_get_resp['title'] == title
    assert incomplete_get_resp['description'] == description
    map_file = incomplete_get_resp['file']
    assert 'status' not in map_file
    assert 'path' in map_file
    with app.app_context():
        assert map_file['url'] == test_util.url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname)
    thumbnail = incomplete_get_resp['thumbnail']
    assert 'status' in thumbnail
    assert thumbnail['status'] in ['PENDING', 'STARTED']

    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_map(workspace=workspace,
                                           name=mapname,
                                           title='abcd',
                                           check_response_fn=empty_method_returns_true,
                                           raise_if_not_complete=False,
                                           )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 49

    process_client.wait_for_publication_status(workspace, process_client.MAP_TYPE, mapname,
                                               check_response_fn=lambda response: not (
                                                   'status' in response.json()['thumbnail'] and response.json()['thumbnail']['status'] in [
                                                       'PENDING', 'STARTED']),
                                               raise_if_not_complete=False,
                                               sleeping_time=0.1,
                                               )

    after_thumbnail_get_resp = process_client.get_workspace_map(workspace=workspace,
                                                                name=mapname,
                                                                )
    thumbnail = after_thumbnail_get_resp['thumbnail']
    assert 'status' not in thumbnail
    assert 'path' in thumbnail
    with app.app_context():
        assert thumbnail['url'] == test_util.url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname)

    file_resp = process_client.get_workspace_map_file(process_client.MAP_TYPE, workspace, mapname)
    assert file_resp['name'] == mapname
    assert file_resp['title'] == title
    assert file_resp['abstract'] == description
    user_json = file_resp['user']
    assert user_json['name'] == workspace
    assert user_json['email'] == ''
    assert len(user_json) == 2
    assert 'groups' not in file_resp

    process_client.wait_for_publication_status(workspace, process_client.MAP_TYPE, mapname,
                                               check_response_fn=lambda response: not (
                                                   'status' in response.json()['metadata'] and response.json()['metadata']['status'] in [
                                                       'PENDING', 'STARTED']),
                                               raise_if_not_complete=False,
                                               sleeping_time=0.1,
                                               )

    with app.app_context():
        expected_md_values = {
            'abstract': "Libovoln\u00fd popis",
            'extent': [
                14.62,
                50.58,
                15.42,
                50.82
            ],
            'graphic_url': test_util.url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname),
            'identifier': {
                "identifier": test_util.url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
                "label": mapname
            },
            'map_endpoint': test_util.url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
            'map_file_endpoint': test_util.url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname),
            'operates_on': [],
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': [
                'EPSG:3857'
            ],
            'revision_date': None,
            'title': "Libereck\u00fd kraj: Administrativn\u00ed \u010dlen\u011bn\u00ed",
        }
    check_metadata(workspace, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)


@pytest.mark.usefixtures('ensure_layman_module')
def test_patch_map():
    workspace = USER
    mapname = MAPNAME_1
    with app.app_context():
        uuid_str = get_publication_uuid(workspace, MAP_TYPE, mapname)
    patch_response = process_client.patch_workspace_map(
        workspace=workspace,
        name=mapname,
        file_paths=['sample/layman.map/full2.json'],
        check_response_fn=empty_method_returns_true,
        raise_if_not_complete=False,
    )
    assert patch_response['uuid'] == uuid_str
    with app.app_context():
        assert patch_response['url'] == test_util.url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname)

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': publication_counter.get()
    })

    incomplete_get_resp = process_client.get_workspace_map(workspace=workspace,
                                                           name=mapname,
                                                           )

    assert incomplete_get_resp['title'] == "Jiné administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
    assert incomplete_get_resp['description'] == "Jiný popis"
    map_file = incomplete_get_resp['file']
    assert 'status' not in map_file
    assert 'path' in map_file
    with app.app_context():
        assert map_file['url'] == test_util.url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname)
    thumbnail = incomplete_get_resp['thumbnail']
    assert 'status' in thumbnail
    assert thumbnail['status'] in ['PENDING', 'STARTED']

    process_client.wait_for_publication_status(workspace, process_client.MAP_TYPE, mapname,
                                               check_response_fn=lambda response: not (
                                                   'status' in response.json()['thumbnail'] and response.json()['thumbnail']['status'] in [
                                                       'PENDING', 'STARTED']),
                                               raise_if_not_complete=False,
                                               sleeping_time=0.1,
                                               )

    after_thumbnail_get_resp = process_client.get_workspace_map(workspace=workspace,
                                                                name=mapname,
                                                                )
    thumbnail = after_thumbnail_get_resp['thumbnail']
    assert 'status' not in thumbnail
    assert 'path' in thumbnail
    with app.app_context():
        assert thumbnail['url'] == test_util.url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname)

    file_resp = process_client.get_workspace_map_file(process_client.MAP_TYPE, workspace, mapname)
    assert file_resp['name'] == mapname
    assert file_resp['title'] == "Jiné administrativn\u00ed \u010dlen\u011bn\u00ed Libereck\u00e9ho kraje"
    assert file_resp['abstract'] == "Jiný popis"
    user_json = file_resp['user']
    assert user_json['name'] == workspace
    assert user_json['email'] == ''
    assert len(user_json) == 2
    assert 'groups' not in file_resp

    process_client.wait_for_publication_status(workspace, process_client.MAP_TYPE, mapname,
                                               check_response_fn=lambda response: not (
                                                   'status' in response.json()['metadata'] and response.json()['metadata']['status'] in [
                                                       'PENDING', 'STARTED']),
                                               raise_if_not_complete=False,
                                               sleeping_time=0.1,
                                               )

    title = 'Nový název'
    process_client.patch_workspace_map(
        workspace=workspace,
        name=mapname,
        title=title,
        check_response_fn=empty_method_returns_true,
        raise_if_not_complete=False,
    )
    get_resp_after_title = process_client.get_workspace_map(workspace=workspace,
                                                            name=mapname,
                                                            )
    assert get_resp_after_title['title'] == "Nový název"
    assert get_resp_after_title['description'] == "Jiný popis"

    description = 'Nový popis'
    process_client.patch_workspace_map(
        workspace=workspace,
        name=mapname,
        description=description,
        check_response_fn=empty_method_returns_true,
        raise_if_not_complete=False,
    )
    get_resp_after_description = process_client.get_workspace_map(workspace=workspace,
                                                                  name=mapname,
                                                                  )
    assert get_resp_after_description['title'] == "Nový název"
    assert get_resp_after_description['description'] == "Nový popis"
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': publication_counter.get()
    })

    with app.app_context():
        expected_md_values = {
            'abstract': "Nov\u00fd popis",
            'extent': [
                14.623,
                50.58,
                15.42,
                50.82
            ],
            'graphic_url': test_util.url_for_external('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname),
            'identifier': {
                "identifier": test_util.url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
                "label": "administrativni_cleneni_libereckeho_kraje"
            },
            'map_endpoint': test_util.url_for_external('rest_workspace_map.get', workspace=workspace, mapname=mapname),
            'map_file_endpoint': test_util.url_for_external('rest_workspace_map_file.get', workspace=workspace, mapname=mapname),
            'operates_on': [],
            'organisation_name': None,
            'publication_date': TODAY_DATE,
            'reference_system': [
                'EPSG:3857'
            ],
            'revision_date': TODAY_DATE,
            'title': "Nov\u00fd n\u00e1zev",
        }
    check_metadata(workspace, mapname, METADATA_PROPERTIES_EQUAL, expected_md_values)
