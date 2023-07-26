import pytest

from db import util as db_util
from layman import app, settings
from test_tools import process_client
from . import upgrade_v1_22

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman', 'oauth2_provider_mock')
def test_fix_issuer_id():
    username = 'test_fix_issuer_id_user'

    headers = process_client.get_authz_headers(username)
    process_client.reserve_username(username, headers=headers)

    statement = f'''update {DB_SCHEMA}.users set issuer_id = 'layman.authn.oauth2.liferay';'''
    with app.app_context():
        db_util.run_statement(statement)

    query = f'''select distinct issuer_id from {DB_SCHEMA}.users;'''
    with app.app_context():
        issuer_id_rows = db_util.run_query(query)
    assert len(issuer_id_rows) == 1
    assert issuer_id_rows[0][0] == 'layman.authn.oauth2.liferay'

    with app.app_context():
        upgrade_v1_22.fix_issuer_id()

    query = f'''select distinct issuer_id from {DB_SCHEMA}.users;'''
    with app.app_context():
        issuer_id_rows = db_util.run_query(query)
    assert len(issuer_id_rows) == 1
    assert issuer_id_rows[0][0] == 'layman.authn.oauth2'
