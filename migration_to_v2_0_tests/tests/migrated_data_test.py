import pytest

from tools.client import RestClient, LAYER_TYPE, MAP_TYPE
from tools.http import LaymanError
from tools.oauth2_provider_mock import OAuth2ProviderMock
from tools.test_data import import_publication_uuids, PUBLICATIONS_TO_MIGRATE, INCOMPLETE_LAYERS, Publication
from tools.test_settings import DB_URI

from db import util as db_util
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
    if isinstance(value, Publication):
        return f"{value.type.replace('layman.', '')}:{value.workspace}:{value.name}"
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
@pytest.mark.parametrize("publication", [
    pytest.param(publ, marks=pytest.mark.xfail(reason="Geoserver provider is not yet migrated"))
    for publ in PUBLICATIONS_TO_MIGRATE if publ.type == LAYER_TYPE
] + [
    publ for publ in PUBLICATIONS_TO_MIGRATE if publ.type == MAP_TYPE
], ids=ids_fn)
def test_complete_status(client, publication):
    publ_detail = client.get_workspace_publication(publication.type, publication.workspace, publication.name,
                                                   actor_name=publication.owner)
    assert publ_detail['layman_metadata']['publication_status'] == 'COMPLETE', f'rest_publication_detail={publ_detail}'


@pytest.mark.usefixtures("import_publication_uuids_fixture")
@pytest.mark.parametrize("layer", INCOMPLETE_LAYERS, ids=ids_fn)
def test_deleted_incomplete_layers(client, layer):
    with pytest.raises(LaymanError) as exc_info:
        client.get_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=layer.owner)
    assert exc_info.value.code == 15
