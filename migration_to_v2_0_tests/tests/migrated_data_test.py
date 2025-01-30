import pytest

from tools.client import RestClient
from tools.oauth2_provider_mock import OAuth2ProviderMock
from tools.test_data import import_publication_uuids, PUBLICATIONS
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


@pytest.mark.usefixtures("import_publication_uuids_fixture", "oauth2_provider_mock_fixture")
def test_migrated_data(client):
    for publ in PUBLICATIONS:
        assert publ.uuid is not None
        publ_detail = client.get_workspace_publication(publ.type, publ.workspace, publ.name, actor_name=publ.owner)
        asserts.assert_description(publ_detail=publ_detail, publication=publ)
