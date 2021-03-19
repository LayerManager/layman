from layman import settings, app as app
from . import users as user_util, workspaces as workspace_util, util as db_util
from .. import prime_db_schema

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def test_get_user_infos():
    with app.app_context():
        user_util.get_user_infos()
        user_util.get_user_infos('test2')
        user_util.get_user_infos('asůldghwíeghsdlkfj')

    username = 'test_ensure_user'
    iss_sub = {'issuer_id': 'mock_test_users_test',
               'sub': '5'}
    userinfo = {**iss_sub,
                "claims": {"email": "test@liferay.com",
                           "name": "test ensure user",
                           "preferred_username": 'test_preferred',
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }
    with app.app_context():
        id_workspace = workspace_util.ensure_workspace(username)
        user_util.ensure_user(id_workspace, userinfo)

        user_infos = user_util.get_user_infos(username)
        assert {username} == user_infos.keys()
        user_infos = user_util.get_user_infos(iss_sub=iss_sub)
        assert {username} == user_infos.keys()


def test_ensure_user():
    username = 'test_ensure_user'
    userinfo = {"issuer_id": 'mock_test_users_test',
                "sub": '10',
                "claims": {"email": "test@liferay.com",
                           "name": "test ensure user",
                           "preferred_username": 'test_preferred',
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }
    sql = f'select us.last_value from {DB_SCHEMA}.users_id_seq us;'
    with app.app_context():
        id_workspace = workspace_util.ensure_workspace(username)
        user_id = user_util.ensure_user(id_workspace, userinfo)
        assert user_id
        user_id2 = user_util.ensure_user(id_workspace, userinfo)
        assert user_id2 == user_id
        prime_db_schema.delete_whole_user(username)

    with app.app_context():
        users_seq_value_1 = db_util.run_query(sql)[0][0]
        (id_workspace, id_user) = prime_db_schema.ensure_whole_user(username, userinfo)
        users_seq_value_2 = db_util.run_query(sql)[0][0]
        assert users_seq_value_2 == id_user,\
            f'users_seq_value_1={users_seq_value_1}, id_user={id_user}, users_seq_value_2={users_seq_value_2}'
        assert users_seq_value_2 == users_seq_value_1 + 1,\
            f'users_seq_value_1={users_seq_value_1}, id_user={id_user}, users_seq_value_2={users_seq_value_2}'
        (_, id_user2) = prime_db_schema.ensure_whole_user(username, userinfo)
        users_seq_value_3 = db_util.run_query(sql)[0][0]
        assert id_user2 == id_user
        assert users_seq_value_3 == users_seq_value_2,\
            f'users_seq_value_1={users_seq_value_1}, id_user={id_user},' \
            f'users_seq_value_2={users_seq_value_2}, users_seq_value_3={users_seq_value_3}'


def test_delete_user():
    user = 'test_delete_user_user'
    workspace = 'test_delete_user_workspace'
    userinfo = {"issuer_id": 'mock_test_users_test',
                "sub": '20',
                "claims": {"email": "test@liferay.com",
                           "preferred_username": 'test_preferred',
                           "name": "test ensure user",
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }

    with app.app_context():
        id_user_workspace = workspace_util.ensure_workspace(user)
        user_util.ensure_user(id_user_workspace, userinfo)

        workspace_util.ensure_workspace(workspace)

        user_util.delete_user(user)
        assert not user_util.get_user_infos(user)
        assert not workspace_util.get_workspace_infos(user)

        user_util.delete_user(workspace)
        assert not user_util.get_user_infos(workspace)
        assert workspace_util.get_workspace_infos(workspace)
