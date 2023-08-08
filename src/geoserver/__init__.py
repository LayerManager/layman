import os
from distutils.dir_util import copy_tree
from urllib.parse import urljoin

GS_AUTH = None
GS_REST = None
GS_REST_STYLES = None
GS_REST_WORKSPACES = None
GS_REST_SETTINGS = None
GS_REST_SECURITY_ACL_LAYERS = None
GS_REST_ROLES = None
GS_REST_USERS = None
GS_REST_USER = None
GS_REST_WMS_SETTINGS = None
GS_REST_WFS_SETTINGS = None
GS_REST_TIMEOUT = None


def ensure_data_dir(data_dir, data_dir_initial, normalized_raster_data_dir):
    if not os.listdir(data_dir):
        copy_tree(data_dir_initial, data_dir)
    norm_data_path = os.path.join(data_dir, normalized_raster_data_dir)
    if not os.path.exists(norm_data_path):
        os.mkdir(norm_data_path)
    os.chmod(norm_data_path, mode=0o777)


def set_settings(gs_url, role_service, user_group_service, timeout):
    role_service = role_service or 'default'
    user_group_service = user_group_service or 'default'
    # pylint: disable=global-statement
    global GS_REST, GS_REST_STYLES, GS_REST_WORKSPACES, GS_REST_SETTINGS, \
        GS_REST_SECURITY_ACL_LAYERS, GS_REST_ROLES, GS_REST_USERS, GS_REST_USER, \
        GS_REST_WMS_SETTINGS, GS_REST_WFS_SETTINGS, GS_REST_TIMEOUT

    GS_REST = urljoin(gs_url, 'rest/')
    GS_REST_STYLES = urljoin(GS_REST, 'styles/')
    GS_REST_WORKSPACES = urljoin(GS_REST, 'workspaces/')
    GS_REST_SETTINGS = urljoin(GS_REST, 'settings/')
    GS_REST_SECURITY_ACL_LAYERS = urljoin(GS_REST, 'security/acl/layers/')
    GS_REST_ROLES = urljoin(GS_REST, f'security/roles/service/{role_service}/')
    GS_REST_USERS = urljoin(GS_REST, f'security/usergroup/service/{user_group_service}/users/')
    GS_REST_USER = urljoin(GS_REST, f'security/usergroup/service/{user_group_service}/user/')
    GS_REST_WMS_SETTINGS = urljoin(GS_REST, f'services/wms/settings/')
    GS_REST_WFS_SETTINGS = urljoin(GS_REST, f'services/wfs/settings/')

    GS_REST_TIMEOUT = timeout
