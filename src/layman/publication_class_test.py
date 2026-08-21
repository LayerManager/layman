import pytest

from layman import app, util as layman_util
from layman.layer import LAYER_TYPE
from layman.layer.layer_class import Layer
from layman.map import MAP_TYPE
from layman.map.map_class import Map
from layman.publication_class import Publication
from test_tools import process_client


PUBLICATION_UUID = '00000000-0000-4000-8000-000000000000'


@pytest.fixture(params=[LAYER_TYPE, MAP_TYPE], ids=['layer', 'map'])
def published_publication(request):
    publ_type = request.param
    publ_type_name = publ_type.split('.')[-1]
    workspace = f'test_publication_class_{publ_type_name}_workspace'
    name = f'test_publication_class_{publ_type_name}'
    uuid = process_client.publish_publication(publ_type, workspace, name)['uuid']

    yield workspace, publ_type, name, uuid

    process_client.delete_publication(publ_type, uuid=uuid)


@pytest.mark.parametrize('publication_type, publication_class', [
    (LAYER_TYPE, Layer),
    (MAP_TYPE, Map),
])
def test_create_by_uuid_and_type(publication_type, publication_class):
    publication = Publication.create(
        uuid=PUBLICATION_UUID,
        publ_type=publication_type,
        load=False,
    )

    assert isinstance(publication, publication_class)
    assert publication.uuid == PUBLICATION_UUID


@pytest.mark.usefixtures('ensure_layman')
def test_get_publication_info_by_uuid(published_publication):
    workspace, publ_type, name, uuid = published_publication
    publication = Publication.create(uuid=uuid, publ_type=publ_type, load=False)

    with app.app_context():
        info = layman_util.get_publication_info(publication, context={'keys': ['id']})

    assert info['uuid'] == uuid
    assert info['_workspace'] == workspace
    assert info['type'] == publ_type
    assert info['name'] == name


@pytest.mark.usefixtures('ensure_layman')
def test_get_publication_info_by_tuple(published_publication):
    workspace, publ_type, name, uuid = published_publication
    publication = Publication.create(publ_tuple=(workspace, publ_type, name), load=False)
    assert not hasattr(publication, 'uuid')

    with app.app_context():
        info = layman_util.get_publication_info(publication, context={'keys': ['id']})

    assert info['uuid'] == uuid
    assert info['_workspace'] == workspace
    assert info['type'] == publ_type
    assert info['name'] == name


@pytest.mark.usefixtures('ensure_layman')
def test_load_publication_by_tuple(published_publication):
    workspace, publ_type, name, uuid = published_publication

    with app.app_context():
        publication = Publication.create(publ_tuple=(workspace, publ_type, name))

    assert publication.uuid == uuid
    assert publication.workspace == workspace
    assert publication.type == publ_type
    assert publication.name == name
    assert publication.exists
