from os import listdir
import json
from string import Template
import pytest

from tools.client import RestClient
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
    exp_input_files = {Template(filename).substitute(uuid=publication.uuid) for filename in publication.exp_input_files}
    input_file_path = f'.{settings.LAYMAN_DATA_DIR}/{publication.type.split(".")[1]}s/{publication.uuid}/input_file/'
    input_files = set(listdir(input_file_path))
    assert exp_input_files == input_files, f'{exp_input_files=}\n{input_files=}'


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("layer", LAYERS_TO_MIGRATE, ids=ids_fn)
def test_layer_thumbnails(client, layer):
    assert layer.exp_thumbnail_path
    img_path = f"tmp/artifacts/migration_to_v2_0_tests/layer_thumbnails/{layer.name}_v2_0.png"
    client.get_layer_thumbnail_by_wms(layer.workspace, layer.name, actor_name=layer.owner, output_path=img_path)

    exp_img_path = layer.exp_thumbnail_path
    diff_pixels = compare_images(img_path, exp_img_path)
    assert diff_pixels <= DEFAULT_THUMBNAIL_PIXEL_DIFF_LIMIT, f"diff_pixels={diff_pixels}\nimg_path={img_path}\nexp_img_path={exp_img_path}"


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("map", MAPS_TO_MIGRATE, ids=ids_fn)
def test_maps_internal_layers(client, map: Map4Test):
    query = f'''
select ml.layer_uuid
from {DB_SCHEMA}.publications map inner join
     {DB_SCHEMA}.map_layer ml on map.id = ml.id_map
where map.uuid = %s
order by ml.id
;
'''
    rows = db_util.run_query(query, data=(map.uuid,), uri_str=DB_URI)
    exp_map_layer_uuids = {layer.uuid for layer in map.exp_internal_layers}
    assert len(rows) == len(exp_map_layer_uuids), f"{rows=}, {exp_map_layer_uuids=}"
    map_layer_uuids = {row[0] for row in rows}
    assert map_layer_uuids == exp_map_layer_uuids, f"{rows=}, {exp_map_layer_uuids=}"

    for layer in map.exp_internal_layers:
        layer_info = client.get_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=layer.owner)
        layer_maps = layer_info['used_in_maps']
        assert {'workspace': map.workspace, 'name': map.name, } in layer_maps, f"{map=}, {layer=}, {layer_maps=}"


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("layer", LAYERS_TO_MIGRATE, ids=ids_fn)
def test_layer_maps(client, layer: Layer4Test):
    layer_info = client.get_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=layer.owner)
    layer_maps = layer_info['used_in_maps']
    exp_maps = [{'workspace': map.workspace, 'name': map.name, } for map in layer.exp_layer_maps]
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
