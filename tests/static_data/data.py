import os
import json
import pytest

from layman import app, settings, util
from layman.common import empty_method_returns_true
from layman.common.prime_db_schema import workspaces
from layman.layer import qgis
from layman.layer.geoserver import wms
from test_tools import process_client, process
from .. import static_data as data, Publication
from ..asserts import util as test_util


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

        layers = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('layers') or []
        for layer_workspace, layer_type, layer in layers:
            ensure_publication(layer_workspace, layer_type, layer)
    elif publ_type == process_client.LAYER_TYPE:
        layer_directory = f'{workspace_directory}/layers/{publication}'
        assert not os.path.exists(layer_directory)
    else:
        assert False, f'Unknown publication type {publ_type}'


@pytest.fixture(scope="session", autouse=True)
def ensure_test_data(oauth2_provider_mock, request):
    # pylint: disable=unused-argument
    yield

    if request.node.testsfailed == 0 and not request.config.option.nocleanup:
        process.ensure_layman_function(process.LAYMAN_DEFAULT_SETTINGS)

        for workspace, publ_type, publication in data.PUBLICATIONS:
            if test_util.get_publication_exists(Publication(workspace, publ_type, publication)):
                headers = data.HEADERS.get(
                    data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])
                process_client.delete_workspace_publication(publ_type, workspace, publication, headers=headers)
                assert_publication_after_delete(workspace, publ_type, publication)


def ensure_all_users():
    with app.app_context():
        workspaces_in_db = workspaces.get_workspace_names()
    for user in data.USERS:
        if user not in workspaces_in_db:
            process_client.ensure_reserved_username(user, headers=data.HEADERS[user])


def ensure_publication(workspace, publ_type, publication):
    ensure_all_users()

    if not test_util.get_publication_exists(Publication(workspace, publ_type, publication)):
        assert_publication_before_post(workspace, publ_type, publication)
        for idx, params in enumerate(data.PUBLICATIONS[(workspace, publ_type, publication)][data.DEFINITION]):
            write_method = process_client.patch_workspace_publication if idx > 0 else process_client.publish_workspace_publication
            write_method(publ_type, workspace, publication, **params)


def check_publication_status(response):
    try:
        current_status = response.json().get('layman_metadata', {}).get('publication_status')
    except json.JSONDecodeError as exc:
        print(f'response={response.text}')
        raise exc
    assert current_status != 'INCOMPLETE', f"{json.dumps(response.json(), indent=2)}"
    return current_status in {'COMPLETE'}


def publish_publications_step(publications_set, step_num):
    done_publications = set()
    write_method = process_client.patch_workspace_publication if step_num > 0 else process_client.publish_workspace_publication
    for workspace, publ_type, publication in publications_set:
        data_def = data.PUBLICATIONS[(workspace, publ_type, publication)][data.DEFINITION]
        params = data_def[step_num]
        write_method(publ_type, workspace, publication, **params, check_response_fn=empty_method_returns_true)
        if len(data_def) == step_num + 1:
            done_publications.add((workspace, publ_type, publication))
    for workspace, publ_type, publication in publications_set:
        params = data.PUBLICATIONS[(workspace, publ_type, publication)][data.DEFINITION][step_num]
        headers = params.get('headers')
        try:
            process_client.wait_for_publication_status(workspace, publ_type, publication, headers=headers, check_response_fn=check_publication_status)
        except AssertionError as ex:
            print(f"AssertionError in publication {workspace, publ_type, publication}, step_num={step_num}.")
            raise ex
    return done_publications


def ensure_all_publications():
    ensure_all_users()
    with app.app_context():
        already_created_publications = util.get_publication_infos()
    publications_to_publish = set(data.PUBLICATIONS) - set(already_created_publications)
    for p_type in [data.LAYER_TYPE, data.MAP_TYPE]:
        publications_by_type = {(workspace, publ_type, publication)
                                for workspace, publ_type, publication in publications_to_publish
                                if publ_type == p_type}
        step_num = 0
        while publications_by_type:
            done_publications = publish_publications_step(publications_by_type, step_num)
            publications_by_type -= done_publications
            step_num += 1
