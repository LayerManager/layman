from layman.common.prime_db_schema import users as users_util, workspaces as workspaces_util

get_usernames = workspaces_util.get_workspace_names


def check_new_layername(username, layername):
    pass


def delete_whole_user(username):
    users_util.delete_user(username)
    workspaces_util.delete_workspace(username)


def ensure_whole_user(username, userinfo=None):
    id_workspace = workspaces_util.ensure_workspace(username)
    if userinfo:
        users_util.ensure_user(id_workspace, userinfo)


def delete_workspace(workspace):
    workspaces_util.delete_workspace(workspace)


def ensure_workspace(workspace):
    workspaces_util.ensure_workspace(workspace)


def check_username(username):
    users_util.check_username(username)
    workspaces_util.check_workspace_name(username)
