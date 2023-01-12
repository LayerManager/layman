from db import util as db_util
from layman import settings, app
from tests import EXTERNAL_DB_NAME

URI = f'''postgresql://{settings.LAYMAN_PG_USER}:{settings.LAYMAN_PG_PASSWORD}@{settings.LAYMAN_PG_HOST}:{settings.LAYMAN_PG_PORT}/{EXTERNAL_DB_NAME}'''


def ensure_db():
    query = f"SELECT count(*) FROM pg_database WHERE datname = %s"
    statement = f"""CREATE DATABASE {EXTERNAL_DB_NAME} TEMPLATE {settings.LAYMAN_PG_TEMPLATE_DBNAME}"""

    with app.app_context():
        res = db_util.run_query(query, (EXTERNAL_DB_NAME,))
        if not res[0][0] == 1:
            db_util.run_statement(statement)


def ensure_table(schema, name, geo_column):
    statement = f'''create table if not exists {schema}.{name} ({geo_column} geometry(Geometry, 4326))'''
    with app.app_context():
        conn_cur = db_util.create_connection_cursor(URI)
        db_util.run_statement(f"""CREATE SCHEMA IF NOT EXISTS "{schema}" AUTHORIZATION {settings.LAYMAN_PG_USER}""", conn_cur=conn_cur)
        db_util.run_statement(statement, conn_cur=conn_cur)
