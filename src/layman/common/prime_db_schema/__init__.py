from layman.common.prime_db_schema import users as users_util, workspaces as workspaces_util
from layman.http import LaymanError

get_usernames = users_util.get_usernames
get_workspaces = workspaces_util.get_workspace_names


def delete_whole_user(username):
    users_util.delete_user(username)
    workspaces_util.delete_workspace(username)


def ensure_whole_user(username, userinfo=None):
    id_workspace = workspaces_util.ensure_workspace(username)
    id_user = None
    if userinfo:
        id_user = users_util.ensure_user(id_workspace, userinfo)
    return id_workspace, id_user


def check_workspace_name(workspace):
    if len(workspace) > 59:
        raise LaymanError(56)
    workspaces_util.check_workspace_name(workspace)
