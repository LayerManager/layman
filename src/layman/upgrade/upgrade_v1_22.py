import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def ensure_issuer_sub_uniqueness():
    logger.info(f'    Ensure (issuer_id, sub) is unique for all users')

    statement = f'''
alter table {DB_SCHEMA}.users
    drop constraint users_sub_key;

alter table {DB_SCHEMA}.users
    add constraint users_issuer_sub_key
        unique (issuer_id, sub);'''

    db_util.run_statement(statement)


def fix_issuer_id():
    logger.info(f'    Fix issuer_id in DB to correct value')

    query = f'''select distinct issuer_id from {DB_SCHEMA}.users;'''
    issuer_id_rows = db_util.run_query(query)
    assert len(issuer_id_rows) <= 1, f"More than one issuer_id was found: {[r[0] for r in issuer_id_rows]}"
    if issuer_id_rows:
        assert issuer_id_rows[0][0] == 'layman.authn.oauth2.liferay', f"Unexpected issuer_id was found: {issuer_id_rows[0][0]}"

    statement = f'''update {DB_SCHEMA}.users set issuer_id = 'layman.authn.oauth2';'''
    db_util.run_statement(statement)
