import json
import pytest

from tools.client import RestClient
from tools.http import LaymanError
from tools.oauth2_provider_mock import OAuth2ProviderMock
from tools.test_data import import_publication_uuids, PUBLICATIONS_TO_MIGRATE, INCOMPLETE_LAYERS, Publication4Test, \
    LAYERS_TO_MIGRATE, WORKSPACES, DEFAULT_THUMBNAIL_PIXEL_DIFF_LIMIT, CREATED_AT_FILE_PATH
from tools.test_settings import DB_URI
from tools.util import compare_images

from db import util as db_util
from geoserver import util as gs_util
import layman_settings as settings


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
