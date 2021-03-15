from layman.common.prime_db_schema import util as db_util


def install_unaccent_to_db():
    statement = '''CREATE EXTENSION IF NOT EXISTS unaccent;
drop index if exists _prime_schema.title_tsv_idx;
drop function if exists _prime_schema.my_unaccent;

CREATE FUNCTION _prime_schema.my_unaccent(text) RETURNS tsvector LANGUAGE SQL IMMUTABLE AS
'SELECT to_tsvector(unaccent($1))';
CREATE INDEX title_tsv_idx ON _prime_schema.publications USING GIST (_prime_schema.my_unaccent(title));
'''
    db_util.run_statement(statement)
