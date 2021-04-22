import os
import pathlib
import shutil

from layman import settings
from layman.util import get_publication_types

PUBL_TYPE_DEF_KEY = '.'.join(__name__.split('.')[:-1])


def get_usernames():
    usersdir = get_workspaces_dir()
    if not os.path.exists(usersdir):
        return []
    user_names = [
        subfile for subfile in os.listdir(usersdir)
        if os.path.isdir(os.path.join(usersdir, subfile))
        and os.path.exists(os.path.join(usersdir, subfile, 'authn.txt'))
    ]
    return user_names


def get_workspaces():
    usersdir = get_workspaces_dir()
    if not os.path.exists(usersdir):
        return []
    user_names = [
        subfile for subfile in os.listdir(usersdir)
        if os.path.isdir(os.path.join(usersdir, subfile))
    ]
    return user_names


def get_workspaces_dir():
    workspacesdir = os.path.join(settings.LAYMAN_DATA_DIR, 'workspaces')
    return workspacesdir


def get_workspace_dir(workspace):
    workspacedir = os.path.join(get_workspaces_dir(), workspace)
    return workspacedir


def ensure_workspace(workspace):
    workspacedir = get_workspace_dir(workspace)
    pathlib.Path(workspacedir).mkdir(exist_ok=True, parents=True)
    return workspacedir


def delete_workspace(workspace):
    workspacedir = get_workspace_dir(workspace)
    try:
        os.rmdir(workspacedir)
    except FileNotFoundError:
        pass


def ensure_whole_user(username):
    ensure_workspace(username)


def delete_whole_user(username):
    delete_workspace(username)


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


def delete_publication_subfile(publ_type, workspace, publ_name, subfile):
    publ_dir = get_publication_dir(publ_type, workspace, publ_name)
    publ_subfile = os.path.join(publ_dir, subfile)
    try:
        os.remove(publ_subfile)
    except OSError:
        pass
    if os.path.exists(publ_dir) and not os.listdir(publ_dir):
        os.rmdir(publ_dir)
    return {}


def delete_publication_subdir(publ_type, workspace, publ_name, subdir):
    publ_dir = get_publication_dir(publ_type, workspace, publ_name)
    publ_subdir = os.path.join(publ_dir, subdir)
    try:
        shutil.rmtree(publ_subdir)
    except FileNotFoundError:
        pass
    if os.path.exists(publ_dir) and not os.listdir(publ_dir):
        os.rmdir(publ_dir)
    return {}
