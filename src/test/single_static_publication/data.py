import os

from layman import util, app, settings
from test_tools import process_client
from .. import single_static_publication as data


def ensure_publication(workspace, publ_type, publication):
    with app.app_context():
        info = util.get_publication_info(workspace, publ_type, publication, context={'keys': ['name']})
    if not info.get('name'):
        workspace_directory = f'{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}'
        layer_directory = f'{workspace_directory}/layers/{publication}'
        assert not os.path.exists(layer_directory)

        for idx, params in enumerate(data.PUBLICATIONS[(workspace, publ_type, publication)][data.DEFINITION]):

            write_method = process_client.patch_workspace_publication if idx > 0 else process_client.publish_workspace_publication
            headers = params.get('headers')
            if headers:
                process_client.ensure_reserved_username(workspace, headers=params['headers'])
            write_method(publ_type, workspace, publication, **params)
