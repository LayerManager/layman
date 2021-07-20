import os

from layman import util, app, settings
from test_tools import process_client
from .. import static_publications as data


def ensure_publication(workspace, publ_type, publication):
    for user in data.USERS:
        process_client.ensure_reserved_username(user, headers=data.HEADERS[user])

    with app.app_context():
        info = util.get_publication_info(workspace, publ_type, publication, context={'keys': ['name']})
    if not info.get('name'):
        if publ_type == process_client.MAP_TYPE:
            layers = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('layers') or list()
            for layer_workspace, layer_type, layer in layers:
                ensure_publication(layer_workspace, layer_type, layer)

        workspace_directory = f'{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}'
        layer_directory = f'{workspace_directory}/layers/{publication}'
        assert not os.path.exists(layer_directory)

        for idx, params in enumerate(data.PUBLICATIONS[(workspace, publ_type, publication)][data.DEFINITION]):
            write_method = process_client.patch_workspace_publication if idx > 0 else process_client.publish_workspace_publication
            write_method(publ_type, workspace, publication, **params)


def ensure_all_publications():
    for workspace, publ_type, publication in data.PUBLICATIONS:
        ensure_publication(workspace, publ_type, publication)
