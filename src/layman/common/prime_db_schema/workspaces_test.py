import pytest

from layman import app as app
from . import users as user_util, workspaces as workspace_util, ensure_whole_user


def test_get_workspace_infos():
    with app.app_context():
        workspace_util.get_workspace_infos()
        workspace_util.get_workspace_infos('test2')
        workspace_util.get_workspace_infos('asůldghwíeghsdlkfj')


def test_ensure_workspace():
    username = 'test_ensure_workspace_user'

    with app.app_context():
        id_workspace = workspace_util.ensure_workspace(username)
        assert id_workspace
        id_user = user_util.get_user_infos(username)
        assert not id_user

        infos = workspace_util.get_workspace_infos()
        assert username in infos
        infos = workspace_util.get_workspace_infos(username)
        assert username in infos

        workspace_util.delete_workspace(username)
        infos = workspace_util.get_workspace_infos()
        assert username not in infos
        infos = workspace_util.get_workspace_infos(username)
        assert username not in infos

        ensure_whole_user(username)
        infos = workspace_util.get_workspace_infos()
        assert username in infos
        infos = workspace_util.get_workspace_infos(username)
        assert username in infos
        id_user = user_util.get_user_infos(username)
        assert not id_user
