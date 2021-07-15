import os

from layman import util, app, settings
from test_tools import process_client
from .. import single_static_publication as data


def ensure_publication(workspace, publ_type, publication):
    for user, headers in data.LIST_USERS:
        process_client.ensure_reserved_username(user, headers=headers)

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
