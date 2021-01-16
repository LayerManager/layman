from layman.common.prime_db_schema import users as users_util, workspaces as workspaces_util

get_usernames = users_util.get_usernames
get_workspaces = workspaces_util.get_workspace_names


def check_new_layername(username, layername):
    pass


def delete_whole_user(username):
    users_util.delete_user(username)
    workspaces_util.delete_workspace(username)


def ensure_whole_user(username, userinfo=None):
    id_workspace = workspaces_util.ensure_workspace(username)
    id_user = None
    if userinfo:
        id_user = users_util.ensure_user(id_workspace, userinfo)
    return id_workspace, id_user


def delete_workspace(workspace):
    workspaces_util.delete_workspace(workspace)


def ensure_workspace(workspace):
    workspaces_util.ensure_workspace(workspace)


def check_username(username):
    users_util.check_username(username)
    workspaces_util.check_workspace_name(username)
