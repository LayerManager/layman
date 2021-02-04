import io
from layman import settings
from layman.http import LaymanError
from layman.common import prime_db_schema
from layman.common import geoserver as gs_common
from layman import util
from layman.layer import LAYER_TYPE
from layman.layer import geoserver
from layman.layer.geoserver import wms


def check_usernames_for_wms_suffix():
    workspaces = prime_db_schema.get_workspaces()
    for workspace in workspaces:
        if workspace.endswith(settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX):
            raise LaymanError(f"A workspace has name with reserved suffix '{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}'. "
                              f"In that case, please downgrade to the previous minor release version of Layman and contact Layman "
                              f"contributors. One way how to do that is to create an issue in Layman repository: "
                              f"https://github.com/jirik/layman/issues/",
                              data={'workspace': workspace,
                                    }
                              )


def migrate_layers_to_wms_workspace(workspace=None):
    infos = util.get_publication_infos(publ_type=LAYER_TYPE, workspace=workspace)
    for (workspace, publication_type, layer) in infos.keys():
        info = util.get_publication_info(workspace, publication_type, layer)
        geoserver_workspace = wms.get_geoserver_workspace(workspace)
        geoserver.ensure_workspace(workspace)

        geoserver.publish_layer_from_db(workspace,
                                        layer,
                                        info.get('description'),
                                        info.get('title'),
                                        info.get('access_rights'),
                                        geoserver_workspace=geoserver_workspace)
        wms.clear_cache(workspace)

        sld_r = gs_common.get_workspace_style_response(workspace, layer, auth=settings.LAYMAN_GS_AUTH)
        sld_stream = io.BytesIO(sld_r.content)
        gs_common.post_workspace_sld_style(geoserver_workspace, layer, sld_stream)
        wms.clear_cache(workspace)

        gs_common.delete_workspace_style(workspace, layer, auth=settings.LAYMAN_GS_AUTH)
