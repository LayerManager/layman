import os
import subprocess
from urllib import parse
from psycopg2 import sql
import pytest
from db import util as db_util
from layman import settings, app
from tests import EXTERNAL_DB_NAME

URI_STR = f'''postgresql://{settings.LAYMAN_PG_USER}:{settings.LAYMAN_PG_PASSWORD}@{settings.LAYMAN_PG_HOST}:{settings.LAYMAN_PG_PORT}/{EXTERNAL_DB_NAME}'''


def uri_str_to_ogr2ogr_str(uri_str):
    uri = parse.urlparse(uri_str)
    return f"PG:host={uri.hostname} port={uri.port} dbname={uri.path[1:]} user={uri.username} password={uri.password}"


@pytest.fixture(scope="session")
def ensure_db():
    statement = f"""CREATE DATABASE {EXTERNAL_DB_NAME} TEMPLATE {settings.LAYMAN_PG_TEMPLATE_DBNAME}"""

    with app.app_context():
        db_util.run_statement(statement)

    yield


def ensure_schema(schema):
    conn_cur = db_util.create_connection_cursor(URI_STR)
    statement = sql.SQL(f'CREATE SCHEMA IF NOT EXISTS {{schema}} AUTHORIZATION {settings.LAYMAN_PG_USER}').format(
        schema=sql.Identifier(schema),
    )
    db_util.run_statement(statement, conn_cur=conn_cur)


def ensure_table(schema, name, geo_column, *, primary_key_columns=None):
    primary_key_columns = ['id'] if primary_key_columns is None else primary_key_columns

    ensure_schema(schema)
    columns = []
    for col in primary_key_columns:
        columns.append(sql.SQL('{column} serial').format(
            column=sql.Identifier(col)
        ))
    columns.append(sql.SQL('{geo_column} geometry(Geometry, 4326)').format(
        geo_column=sql.Identifier(geo_column)
    ))
    if primary_key_columns:
        columns.append(sql.SQL('PRIMARY KEY ({columns})').format(
            columns=sql.SQL(',').join(sql.Identifier(c) for c in primary_key_columns)
        ))

    statement = sql.SQL('create table {table} ({columns})').format(
        table=sql.Identifier(schema, name),
        columns=sql.SQL(',').join(columns),
    )
    conn_cur = db_util.create_connection_cursor(URI_STR)
    db_util.run_statement(statement, conn_cur=conn_cur)


def import_table(input_file_path, *, table=None, schema='public', geo_column='wkb_geometry',
                 primary_key_column=settings.OGR_DEFAULT_PRIMARY_KEY):
    table = table or os.path.splitext(os.path.basename(input_file_path))[0]
    primary_key_to_later_drop = 'pk_to_drop'

    ensure_schema(schema)

    target_db = uri_str_to_ogr2ogr_str(URI_STR)

    bash_args = [
        'ogr2ogr',
        '-nln', table,
        '-lco', f'SCHEMA={schema}',
        '-lco', f'LAUNDER=NO',
        '-lco', f'EXTRACT_SCHEMA_FROM_LAYER_NAME=NO',
        '-lco', f'GEOMETRY_NAME={geo_column}',
        '-lco', f"FID={primary_key_column if primary_key_column is not None else primary_key_to_later_drop}",
        '-f', 'PostgreSQL',
        target_db,
        input_file_path,
    ]

    process = subprocess.Popen(bash_args, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    return_code = process.poll()
    assert return_code == 0 and not stdout and not stderr, f"return_code={return_code}, stdout={stdout}, stderr={stderr}"

    if primary_key_column is None:
        conn_cur = db_util.create_connection_cursor(URI_STR)
        statement = sql.SQL("alter table {table} drop column {primary_key}").format(
            table=sql.Identifier(schema, table),
            primary_key=sql.Identifier(primary_key_to_later_drop),
        )
        db_util.run_statement(statement, conn_cur=conn_cur)


def drop_table(schema, name):
    statement = sql.SQL('drop table {table}').format(
        table=sql.Identifier(schema, name)
    )
    conn_cur = db_util.create_connection_cursor(URI_STR)
    db_util.run_statement(statement, conn_cur=conn_cur)
