import pytest

from layman import app, uuid, LaymanError
from layman.util import SimpleCounter
from test_tools import process_client
from . import MAP_TYPE

publication_counter = SimpleCounter()


@pytest.mark.usefixtures('ensure_layman_module')
def test_get_maps_empty():
    workspace = 'testuser1'
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
    workspace = 'testuser1'
    with pytest.raises(LaymanError) as exc_info:
        process_client.get_workspace_map(workspace=workspace,
                                         name=mapname,
                                         )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 2
    assert exc_info.value.data['parameter'] == 'mapname'


@pytest.mark.usefixtures('ensure_layman_module')
def test_no_file():
    workspace = 'testuser1'
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
    workspace = 'testuser1'
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
    workspace = 'testuser1'
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
