from layman import app, settings
from . import users as user_util, workspaces as workspace_util, ensure_whole_user, util as db_util

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def test_get_workspace_infos():
    with app.app_context():
        workspace_util.get_workspace_infos()
        workspace_util.get_workspace_infos('test2')
        workspace_util.get_workspace_infos('asůldghwíeghsdlkfj')


def test_ensure_workspace():
    username = 'test_ensure_workspace_user'
    sql = f'select ws.last_value from {DB_SCHEMA}.workspaces_id_seq ws;'

    with app.app_context():
        id_workspace = workspace_util.ensure_workspace(username)
        assert id_workspace
        id_user = user_util.get_user_infos(username)
        assert not id_user
        workspaces_seq_value_1 = db_util.run_query(sql)[0][0]
        assert workspaces_seq_value_1 == id_workspace,\
            f'workspaces_seq_value_1={workspaces_seq_value_1}, id_workspace={id_workspace}'

        id_workspace2 = workspace_util.ensure_workspace(username)
        assert id_workspace == id_workspace2
        workspaces_seq_value_2 = db_util.run_query(sql)[0][0]
        assert workspaces_seq_value_2 == workspaces_seq_value_1,\
            f'workspaces_seq_value_1={workspaces_seq_value_1}, id_workspace={id_workspace}, workspaces_seq_value_2={workspaces_seq_value_2}'

        infos = workspace_util.get_workspace_infos()
        assert username in infos
        assert infos[username]['id'] == id_workspace
        infos = workspace_util.get_workspace_infos(username)
        assert username in infos
        assert infos[username]['id'] == id_workspace

        workspace_util.delete_workspace(username)
        infos = workspace_util.get_workspace_infos()
        assert username not in infos
        infos = workspace_util.get_workspace_infos(username)
        assert username not in infos

        ensure_whole_user(username)
        workspaces_seq_value_3 = db_util.run_query(sql)[0][0]
        assert workspaces_seq_value_3 == workspaces_seq_value_2 + 1,\
            f'workspaces_seq_value_1={workspaces_seq_value_1}, id_workspace={id_workspace},' \
            f'workspaces_seq_value_2={workspaces_seq_value_2}, workspaces_seq_value_3={workspaces_seq_value_3}'
        infos = workspace_util.get_workspace_infos()
        assert username in infos
        infos = workspace_util.get_workspace_infos(username)
        assert username in infos
        id_user = user_util.get_user_infos(username)
        assert not id_user
