from layman import settings
from layman.http import LaymanError
from layman.common import prime_db_schema


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
