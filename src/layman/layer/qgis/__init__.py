import os
import pathlib
import shutil
from functools import partial

from layman import settings
from layman.common import empty_method
from layman.util import get_publication_types
from layman.layer import LAYER_TYPE

PUBL_TYPE_DEF_KEY = __name__

check_workspace_name = empty_method


def get_workspaces_dir():
    workspace_sdir = os.path.join(settings.LAYMAN_QGIS_DATA_DIR, 'workspaces')
    return workspace_sdir


def get_workspace_dir(workspace):
    workspace_dir = os.path.join(get_workspaces_dir(), workspace)
    return workspace_dir


def ensure_whole_user(username):
    ensure_workspace(username)


def delete_whole_user(username):
    delete_workspace(username)


def ensure_workspace(workspace):
    workspace_dir = get_workspace_dir(workspace)
    pathlib.Path(workspace_dir).mkdir(exist_ok=True, parents=True)
    return workspace_dir


def delete_workspace(workspace):
    workspace_dir = get_workspace_dir(workspace)
    try:
        shutil.rmtree(workspace_dir)
        os.rmdir(workspace_dir)
    except FileNotFoundError:
        pass


def get_usernames():
    return []


def get_workspaces():
    workspaces_dir = get_workspaces_dir()
    if not os.path.exists(workspaces_dir):
        return []
    workspace = [
        subfile for subfile in os.listdir(workspaces_dir)
        if os.path.isdir(os.path.join(workspaces_dir, subfile))
    ]
    return workspace


def get_publications_dir(publ_type, workspace):
    publ_types = get_publication_types()
    dirname = publ_types[publ_type][PUBL_TYPE_DEF_KEY]['publications_dir']
    layersdir = os.path.join(get_workspace_dir(workspace), dirname)
    return layersdir


def get_publication_dir(publ_type, workspace, publ_name):
    publ_dir = os.path.join(
        get_publications_dir(publ_type, workspace),
        publ_name
    )
    return publ_dir


def ensure_publication_dir(publ_type, workspace, publ_name):
    publ_dir = get_publication_dir(publ_type, workspace, publ_name)
    pathlib.Path(publ_dir).mkdir(exist_ok=True, parents=True)
    return publ_dir


def delete_publication_dir(publ_type, workspace, publ_name):
    publ_dir = get_publication_dir(publ_type, workspace, publ_name)
    try:
        shutil.rmtree(publ_dir)
    except FileNotFoundError:
        pass
    if os.path.exists(publ_dir) and not os.listdir(publ_dir):
        os.rmdir(publ_dir)
    return {}


get_layers_dir = partial(get_publications_dir, LAYER_TYPE)

get_layer_dir = partial(get_publication_dir, LAYER_TYPE)

ensure_layer_dir = partial(ensure_publication_dir, LAYER_TYPE)

delete_layer_dir = partial(delete_publication_dir, LAYER_TYPE)
