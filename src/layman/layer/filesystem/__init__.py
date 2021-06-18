from layman.common import empty_method
from layman.common.filesystem import util as common_util
from . import util

check_username = empty_method
check_new_layername = empty_method

get_usernames = common_util.get_usernames
get_workspaces = common_util.get_workspaces
ensure_workspace = common_util.ensure_workspace
ensure_whole_user = common_util.ensure_whole_user


def delete_workspace(workspace):
    common_util.delete_workspace(workspace)
    util.delete_normalized_raster_workspace(workspace)


delete_whole_user = delete_workspace
