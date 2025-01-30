import pytest

from tools.client import RestClient
from tools.oauth2_provider_mock import OAuth2ProviderMock
from tools.test_data import import_publication_uuids, PUBLICATIONS, Publication
from . import asserts


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


@pytest.mark.usefixtures("import_publication_uuids_fixture", "oauth2_provider_mock_fixture")
@pytest.mark.parametrize("publication", PUBLICATIONS, ids=ids_fn)
def test_migrated_description(client, publication):
    assert publication.uuid is not None
    publ_detail = client.get_workspace_publication(publication.type, publication.workspace, publication.name,
                                                   actor_name=publication.owner)
    asserts.assert_description(publ_detail=publ_detail, publication=publication)
