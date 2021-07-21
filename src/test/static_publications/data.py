import os

from layman import util, app, settings
from layman.common.prime_db_schema import workspaces
from test_tools import process_client
from .. import static_publications as data


def ensure_publication(workspace, publ_type, publication):
    with app.app_context():
        workspaces_in_db = workspaces.get_workspace_names()
    for user in data.USERS:
        if user not in workspaces_in_db:
            process_client.ensure_reserved_username(user, headers=data.HEADERS[user])

    with app.app_context():
        info = util.get_publication_info(workspace, publ_type, publication, context={'keys': ['name']})
    if not info.get('name'):
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

        for idx, params in enumerate(data.PUBLICATIONS[(workspace, publ_type, publication)][data.DEFINITION]):
            write_method = process_client.patch_workspace_publication if idx > 0 else process_client.publish_workspace_publication
            write_method(publ_type, workspace, publication, **params)


def ensure_all_publications():
    for workspace, publ_type, publication in data.PUBLICATIONS:
        ensure_publication(workspace, publ_type, publication)
