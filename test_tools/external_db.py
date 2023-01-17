import os
import subprocess
from urllib import parse
import pytest
from db import util as db_util
from layman import settings, app
from tests import EXTERNAL_DB_NAME

URI = f'''postgresql://{settings.LAYMAN_PG_USER}:{settings.LAYMAN_PG_PASSWORD}@{settings.LAYMAN_PG_HOST}:{settings.LAYMAN_PG_PORT}/{EXTERNAL_DB_NAME}'''


def uri_to_ogr2ogr(uri_str):
    uri = parse.urlparse(uri_str)
    return f"PG:host={uri.hostname} port={uri.port} dbname={uri.path[1:]} user={uri.username} password={uri.password}"


@pytest.fixture(scope="session")
def ensure_db():
    statement = f"""CREATE DATABASE {EXTERNAL_DB_NAME} TEMPLATE {settings.LAYMAN_PG_TEMPLATE_DBNAME}"""

    with app.app_context():
        db_util.run_statement(statement)

    yield


def ensure_table(schema, name, geo_column):
    statement = f'''create table {schema}.{name} ({geo_column} geometry(Geometry, 4326))'''
    conn_cur = db_util.create_connection_cursor(URI)
    db_util.run_statement(f"""CREATE SCHEMA IF NOT EXISTS "{schema}" AUTHORIZATION {settings.LAYMAN_PG_USER}""", conn_cur=conn_cur)
    db_util.run_statement(statement, conn_cur=conn_cur)


def import_table(input_file_path, *, table=None, schema='public'):
    table = table or os.path.splitext(os.path.basename(input_file_path))[0]
    target_db = uri_to_ogr2ogr(URI)

    bash_args = [
        'ogr2ogr',
        '-nln', table,
        # '-nlt', 'GEOMETRY',
        '-lco', f'SCHEMA={schema}',
        '-f', 'PostgreSQL',
        target_db,
        input_file_path,
    ]

    process = subprocess.Popen(bash_args, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    return_code = process.poll()
    assert return_code == 0 and not stdout and not stderr


def drop_table(schema, name):
    statement = f'''drop table if exists {schema}.{name}'''
    conn_cur = db_util.create_connection_cursor(URI)
    db_util.run_statement(statement, conn_cur=conn_cur)
