import pytest
from db import util as db_util
from layman import settings, app
from tests import EXTERNAL_DB_NAME

URI = f'''postgresql://{settings.LAYMAN_PG_USER}:{settings.LAYMAN_PG_PASSWORD}@{settings.LAYMAN_PG_HOST}:{settings.LAYMAN_PG_PORT}/{EXTERNAL_DB_NAME}'''


@pytest.fixture(scope="session")
def ensure_db():
    statement = f"""CREATE DATABASE {EXTERNAL_DB_NAME} TEMPLATE {settings.LAYMAN_PG_TEMPLATE_DBNAME}"""

    with app.app_context():
        db_util.run_statement(statement)

    yield


def ensure_table(schema, name, geo_column):
    statement = f'''create table {schema}.{name} ({geo_column} geometry(Geometry, 4326))'''
    with app.app_context():
        conn_cur = db_util.create_connection_cursor(URI)
        db_util.run_statement(f"""CREATE SCHEMA IF NOT EXISTS "{schema}" AUTHORIZATION {settings.LAYMAN_PG_USER}""", conn_cur=conn_cur)
        db_util.run_statement(statement, conn_cur=conn_cur)


def drop_table(schema, name):
    statement = f'''drop table if exists {schema}.{name}'''
    with app.app_context():
        conn_cur = db_util.create_connection_cursor(URI)
        db_util.run_statement(statement, conn_cur=conn_cur)
