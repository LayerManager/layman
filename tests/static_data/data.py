import os
import pytest

from layman import util, app, settings
from layman.common.prime_db_schema import workspaces
from layman.layer import qgis
from layman.layer.geoserver import wms
from test_tools import process_client, process
from .. import static_data as data


def assert_publication_after_delete(workspace, publ_type, publication):
    publication_dir_name = publ_type.split('.')[-1] + 's'
    workspace_directory = f'{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}'
    publication_directory = f'{workspace_directory}/{publication_dir_name}/{publication}'
    assert not os.path.exists(publication_directory)

    if publ_type == process_client.LAYER_TYPE:
        with app.app_context():
            assert wms.get_layer_info(workspace, publication) == {}
        if data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['style_type'] == 'qml':
            assert workspace in qgis.get_workspaces()


def assert_publication_before_post(workspace, publ_type, publication):
    workspace_directory = f'{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}'
    if publ_type == process_client.MAP_TYPE:
        map_directory = f'{workspace_directory}/maps/{publication}'
        assert not os.path.exists(map_directory)

        layers = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('layers') or list()
        for layer_workspace, layer_type, layer in layers:
            ensure_publication(layer_workspace, layer_type, layer)
    elif publ_type == process_client.LAYER_TYPE:
        layer_directory = f'{workspace_directory}/layers/{publication}'
        assert not os.path.exists(layer_directory)
    else:
        assert False, f'Unknown publication type {publ_type}'


@pytest.fixture(scope="session", autouse=True)
def ensure_test_data(liferay_mock, request):
    # pylint: disable=unused-argument
    yield

    if request.node.testsfailed == 0:
        process.ensure_layman_function(process.LAYMAN_DEFAULT_SETTINGS)
        with app.app_context():
            info = util.get_publication_infos()

        for workspace, publ_type, publication in info:
            headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])
            process_client.delete_workspace_publication(publ_type, workspace, publication, headers=headers)
            assert_publication_after_delete(workspace, publ_type, publication)


def ensure_publication(workspace, publ_type, publication):
    with app.app_context():
        workspaces_in_db = workspaces.get_workspace_names()
    for user in data.USERS:
        if user not in workspaces_in_db:
            process_client.ensure_reserved_username(user, headers=data.HEADERS[user])

    with app.app_context():
        info = util.get_publication_info(workspace, publ_type, publication, context={'keys': ['name']})
    if not info.get('name'):
        assert_publication_before_post(workspace, publ_type, publication)
        for idx, params in enumerate(data.PUBLICATIONS[(workspace, publ_type, publication)][data.DEFINITION]):
            write_method = process_client.patch_workspace_publication if idx > 0 else process_client.publish_workspace_publication
            write_method(publ_type, workspace, publication, **params)


def ensure_all_publications():
    for workspace, publ_type, publication in data.PUBLICATIONS:
        ensure_publication(workspace, publ_type, publication)
