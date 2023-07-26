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
