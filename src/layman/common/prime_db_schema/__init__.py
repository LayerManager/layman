from layman.common.prime_db_schema import users as users_util, workspaces as workspaces_util

get_usernames = workspaces_util.get_workspace_names
check_username = users_util.check_username


def check_new_layername(username, layername):
    pass


def delete_whole_user(username):
    users_util.delete_user(username)
    workspaces_util.delete_workspace(username)


def ensure_whole_user(username, userinfo=None):
    id_workspace = workspaces_util.ensure_workspace(username)
    if userinfo != {} and userinfo is not None:
        users_util.ensure_user(id_workspace, userinfo)


def check_username(username):
    users_util.check_username(username)
    workspaces_util.check_workspace_name(username)
