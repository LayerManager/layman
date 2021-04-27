from layman.common import empty_method

ensure_whole_user = empty_method
delete_whole_user = empty_method
ensure_workspace = empty_method
delete_workspace = empty_method
check_username = empty_method
check_new_layername = empty_method


def get_usernames():
    # TODO consider reading layer names from all Micka's metadata records by linkage URL
    return []


get_workspaces = get_usernames
