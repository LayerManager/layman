from os import listdir, path
from datetime import datetime
import json
from string import Template
from typing import List
import pytest

from tools.client import RestClient, LAYER_TYPE, MAP_TYPE
from tools.http import LaymanError
from tools.oauth2_provider_mock import OAuth2ProviderMock
from tools.test_data import import_publication_uuids, PUBLICATIONS_TO_MIGRATE, INCOMPLETE_LAYERS, Publication4Test, \
    LAYERS_TO_MIGRATE, WORKSPACES, DEFAULT_THUMBNAIL_PIXEL_DIFF_LIMIT, CREATED_AT_FILE_PATH, \
    LAYERS_TO_MIGRATE_VECTOR_INTERNAL_DB, MAPS_TO_MIGRATE, Map4Test, Layer4Test
from tools.test_settings import DB_URI
from tools.util import compare_images

from db import util as db_util
from geoserver import util as gs_util
import layman_settings as settings


DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
MAPS_FOR_THUMBNAIL_TEST: List[Map4Test] = [map for map in MAPS_TO_MIGRATE if map.exp_internal_layers and map.exp_thumbnail_path]
MAPS_FOR_INPUT_FILE_TEST: List[Map4Test] = [map for map in MAPS_TO_MIGRATE if map.exp_input_file and map.exp_internal_layers]

LAYER_METADATA_PROPERTIES = {
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
    # 'spatial_resolution',  # It is not updated for vector layer updated as raster one (probably because of bug in Micka)
    'temporal_extent',
    'title',
    'wfs_url',
    'wms_url',
}

MAP_METADATA_PROPERTIES = {
    'abstract',
    'extent',
    'graphic_url',
    'identifier',
    'map_endpoint',
    'map_file_endpoint',
    'operates_on',  # When sending map with no items after there were some items, items are not deleted (probably because of bug in Micka)
    'organisation_name',
    'publication_date',
    'reference_system',
    'revision_date',
    'title',
}


@pytest.fixture(scope="session")
def import_publication_uuids_fixture():
    import_publication_uuids()


@pytest.fixture(scope="session")
def oauth2_provider_mock_fixture():
    with OAuth2ProviderMock():
        yield


@pytest.fixture(scope="session", name="client")
def client_fixture():
    client = RestClient("http://localhost:8000")
    yield client


def ids_fn(value):
    if isinstance(value, Publication4Test):
        return f"{value.type.replace('layman.', '')}:{value.workspace}:{value.name}"
    if isinstance(value, str):
        return value
    return None


@pytest.mark.usefixtures("import_publication_uuids_fixture", "oauth2_provider_mock_fixture")
@pytest.mark.parametrize("publication", PUBLICATIONS_TO_MIGRATE, ids=ids_fn)
def test_migrated_description(client, publication):
    assert publication.uuid is not None
    publ_detail = client.get_workspace_publication(publication.type, publication.workspace, publication.name,
                                                   actor_name=publication.owner)
    assert publ_detail['description'] == publication.rest_args['description']

    rows = db_util.run_query(f"select description from {settings.LAYMAN_PRIME_SCHEMA}.publications where uuid = %s",
                             data=(publication.uuid,), uri_str=DB_URI)
    assert len(rows) == 1
    assert rows[0][0] == publication.rest_args['description']


@pytest.mark.usefixtures("import_publication_uuids_fixture", "oauth2_provider_mock_fixture")
@pytest.mark.parametrize("publication", PUBLICATIONS_TO_MIGRATE, ids=ids_fn)
def test_complete_status(client, publication):
    publ_detail = client.get_workspace_publication(publication.type, publication.workspace, publication.name,
                                                   actor_name=publication.owner)
    assert publ_detail['layman_metadata']['publication_status'] == 'COMPLETE', f'rest_publication_detail={publ_detail}'


@pytest.mark.usefixtures("import_publication_uuids_fixture", "oauth2_provider_mock_fixture")
@pytest.mark.parametrize("publication", PUBLICATIONS_TO_MIGRATE, ids=ids_fn)
def test_created_at(publication):
    rows = db_util.run_query(f"select created_at from {settings.LAYMAN_PRIME_SCHEMA}.publications where uuid = %s",
                             data=(publication.uuid,), uri_str=DB_URI)
    assert len(rows) == 1
    with open(CREATED_AT_FILE_PATH, encoding='utf-8') as uuid_file:
        publ_created_at = json.load(uuid_file)
    assert rows[0][0].isoformat() == publ_created_at[publication.uuid]


@pytest.mark.usefixtures("import_publication_uuids_fixture", "oauth2_provider_mock_fixture")
@pytest.mark.parametrize("publication", PUBLICATIONS_TO_MIGRATE, ids=ids_fn)
def test_input_files(publication):
    input_file_path = f'.{settings.LAYMAN_DATA_DIR}/{publication.type.split(".")[1]}s/{publication.uuid}/input_file/'
    if publication.exp_input_files is not None:
        exp_input_files = {Template(filename).substitute(uuid=publication.uuid) for filename in publication.exp_input_files}
        input_files = set(listdir(input_file_path))
        assert exp_input_files == input_files, f'{exp_input_files=}\n{input_files=}'
    else:
        assert not path.exists(input_file_path), f'{input_file_path=}'


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("layer", LAYERS_TO_MIGRATE, ids=ids_fn)
def test_layer_thumbnails(client, layer):
    assert layer.exp_thumbnail_path
    img_path = f"tmp/artifacts/migration_to_v2_0_tests/layer_thumbnails/{layer.name}_v2_0.png"
    client.get_layer_thumbnail_by_wms(layer.workspace, layer.name, actor_name=layer.owner, output_path=img_path)

    exp_img_path = layer.exp_thumbnail_path
    diff_pixels = compare_images(img_path, exp_img_path)
    assert diff_pixels <= DEFAULT_THUMBNAIL_PIXEL_DIFF_LIMIT, f"diff_pixels={diff_pixels}\nimg_path={img_path}\nexp_img_path={exp_img_path}"


def get_map_thumbnail_timestamp(publication: Publication4Test):
    thumbnail_file_path = f"./layman_data/{publication.type.split('.')[1]}s/{publication.uuid}/thumbnail/{publication.uuid}.png"
    thumbnail_timestamp = datetime.fromtimestamp(path.getmtime(thumbnail_file_path))
    return thumbnail_timestamp


@pytest.mark.usefixtures("import_publication_uuids_fixture", "oauth2_provider_mock_fixture")
@pytest.mark.parametrize("map", MAPS_FOR_THUMBNAIL_TEST, ids=ids_fn)
def test_maps_thumbnail(client, map: Map4Test):
    # Check map thumbnail
    thumbnail_path = f'.{settings.LAYMAN_DATA_DIR}/maps/{map.uuid}/thumbnail/{map.uuid}.png'
    exp_img_path = map.exp_thumbnail_path
    diff_pixels = compare_images(thumbnail_path, exp_img_path)
    assert diff_pixels <= DEFAULT_THUMBNAIL_PIXEL_DIFF_LIMIT, f"{diff_pixels=}\n{thumbnail_path=}\n{exp_img_path=}"

    # Trigger thumbnail re-generation
    layer = next(iter(next(iter(map.exp_internal_layers.values()))))
    file_paths = layer.rest_args['file_paths']
    pre_thumbnail_timestamp = get_map_thumbnail_timestamp(map)
    client.patch_workspace_publication(layer.type,
                                       layer.workspace,
                                       layer.name,
                                       actor_name=layer.owner,
                                       file_paths=file_paths,
                                       )
    client.wait_for_publication_status(map.workspace, map.type, map.name, actor_name=map.owner)

    # Check thumbnail was re-generated
    post_thumbnail_timestamp = get_map_thumbnail_timestamp(map)
    assert post_thumbnail_timestamp > pre_thumbnail_timestamp

    # Check new map thumbnail
    diff_pixels = compare_images(thumbnail_path, exp_img_path)
    assert diff_pixels <= DEFAULT_THUMBNAIL_PIXEL_DIFF_LIMIT, f"{diff_pixels=}\n{thumbnail_path=}\n{exp_img_path=}"


@pytest.mark.usefixtures("import_publication_uuids_fixture", "oauth2_provider_mock_fixture")
@pytest.mark.parametrize("map", MAPS_FOR_INPUT_FILE_TEST, ids=ids_fn)
def test_maps_input_file(map: Map4Test):
    with open(map.exp_input_file, 'r', encoding="utf-8") as map_file:
        src_map_file = map_file.read()

    # Replace layers' UUIDs
    template_mapping = {}
    layers = [layer for layers in map.exp_internal_layers.values() for layer in layers]
    for idx, layer in enumerate(layers):
        template_mapping[f'uuid{idx}'] = layer.uuid

    exp_input_file_txt = Template(src_map_file).substitute(**template_mapping)
    exp_input_file = json.loads(exp_input_file_txt)

    input_file_path = f'.{settings.LAYMAN_DATA_DIR}/maps/{map.uuid}/input_file/{map.uuid}.json'
    with open(input_file_path, 'r', encoding="utf-8") as map_file:
        input_file = json.load(map_file)
    assert exp_input_file == input_file


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("map", MAPS_TO_MIGRATE, ids=ids_fn)
def test_maps_internal_layers(client, map: Map4Test):
    query = f'''
select layer_index, layers
from (
    select ml.layer_index, json_agg(ml.layer_uuid order by ml.layer_uuid) layers
    from {DB_SCHEMA}.publications map inner join
         {DB_SCHEMA}.map_layer ml on map.id = ml.id_map
    where map.uuid = %s
    group by ml.layer_index
    order by ml.layer_index) tab
;
'''
    rows = db_util.run_query(query, data=(map.uuid,), uri_str=DB_URI)
    map_layers = dict(rows)
    exp_map_internal_layers = {layer_index: sorted([layer.uuid for layer in layers]) for layer_index, layers in map.exp_internal_layers.items()}
    assert map_layers == exp_map_internal_layers, f"{map_layers=}, {exp_map_internal_layers=}"

    map_layers_set = [layer for layers in map.exp_internal_layers.values() for layer in layers]
    for layer in map_layers_set:
        layer_info = client.get_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=layer.owner)
        layer_maps = layer_info['used_in_maps']
        assert {'workspace': map.workspace, 'name': map.name, } in layer_maps, f"{map=}, {layer=}, {layer_maps=}"


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("layer", LAYERS_TO_MIGRATE, ids=ids_fn)
def test_layer_maps(client, layer: Layer4Test):
    layer_info = client.get_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=layer.owner)
    layer_maps = layer_info['used_in_maps']
    exp_maps = [{'workspace': map.workspace, 'name': map.name, } for map in layer.exp_layer_maps]
    layer_maps.sort(key=lambda x: (x['workspace'], x['name']))
    exp_maps.sort(key=lambda x: (x['workspace'], x['name']))
    assert layer_maps == exp_maps, f"{layer_maps=}, {map=}"


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("layer", INCOMPLETE_LAYERS, ids=ids_fn)
def test_deleted_incomplete_layers(client, layer):
    with pytest.raises(LaymanError) as exc_info:
        client.get_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=layer.owner)
    assert exc_info.value.code == 15
    rows = db_util.run_query(f"select * from {settings.LAYMAN_PRIME_SCHEMA}.publications where uuid = %s",
                             data=(layer.uuid,), uri_str=DB_URI)
    assert len(rows) == 0


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("publication", PUBLICATIONS_TO_MIGRATE, ids=ids_fn)
def test_metadata_comparison(client, publication):
    md_props = {
        LAYER_TYPE: LAYER_METADATA_PROPERTIES,
        MAP_TYPE: MAP_METADATA_PROPERTIES,
    }[publication.type]

    metadata_comparison_json = client.get_workspace_publication_metadata_comparison(publication.type,
                                                                                    publication.workspace,
                                                                                    publication.name,
                                                                                    actor_name=publication.owner)

    assert md_props.issubset(set(metadata_comparison_json['metadata_properties'].keys()))
    for key, value in metadata_comparison_json['metadata_properties'].items():
        if key == 'graphic_url':
            # Since version 3.0+, the thumbnail URL format has changed (UUID-based instead of workspace/name),
            # so the difference is expected and should be ignored in this comparison.
            continue
        assert value['equal_or_null'] is True, f'{key=}, {value=}\n{metadata_comparison_json=}'
        assert value['equal'] is True, f'{key=}, {value=}\n{metadata_comparison_json=}'


@pytest.mark.parametrize("geoserver_workspace", ["layman", "layman_wms"], ids=ids_fn)
def test_workspaces_created(geoserver_workspace):
    found_ws = gs_util.get_workspace(geoserver_workspace, auth=settings.LAYMAN_GS_AUTH)
    assert found_ws is not None, f"GeoServer workspace {geoserver_workspace} should be created, but it is not."


@pytest.mark.parametrize("layman_workspace", WORKSPACES, ids=ids_fn)
def test_workspaces_deleted(layman_workspace):
    for gs_workspace in [layman_workspace, f"{layman_workspace}_wms"]:
        found_ws = gs_util.get_workspace(layman_workspace, auth=settings.LAYMAN_GS_AUTH)
        assert found_ws is None, f"GeoServer workspace {gs_workspace} should be deleted, but it is not."


def test_schemas_deleted():
    rows = db_util.run_query(f"""
select schema_name
from information_schema.schemata
order by schema_name;
""", uri_str=DB_URI)
    exp_schema_names = [
        '_prime_schema',
        '_role_service',
        'information_schema',
        'layers',
        'pg_catalog',
        'pg_toast',
        'public',
    ]
    schema_names = [row[0] for row in rows]
    assert schema_names == exp_schema_names


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("layer", LAYERS_TO_MIGRATE_VECTOR_INTERNAL_DB, ids=ids_fn)
def test_layer_table_in_internal_db(layer):
    table_name = f"layer_{layer.uuid.replace('-', '_')}"
    db_util.run_query(f"""
    select * from layers.{table_name}
    """, uri_str=DB_URI)
