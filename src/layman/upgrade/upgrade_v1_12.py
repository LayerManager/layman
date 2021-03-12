from layman.common.prime_db_schema import util as db_util


def install_unaccent_to_db():
    statement = 'CREATE EXTENSION IF NOT EXISTS unaccent;'
    db_util.run_statement(statement)
