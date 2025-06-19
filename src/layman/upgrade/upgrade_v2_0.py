import logging
from psycopg2 import sql

from db import util as db_util
from geoserver import util as gs_util
from layman import settings
from layman.layer import db as layer_db
from layman.layer.geoserver import GEOSERVER_WMS_WORKSPACE, GEOSERVER_WFS_WORKSPACE
from layman.layer.geoserver.util import DEFAULT_INTERNAL_DB_STORE

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_description():
    logger.info(f'    Alter DB prime schema for description')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS
    description varchar(1024) default null;'''
    db_util.run_statement(statement)


def adjust_db_for_map_layer_relation():
    logger.info(f'    Alter DB prime schema map_layer table for UUID')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.map_layer ADD COLUMN IF NOT EXISTS
    layer_uuid  uuid default null;'''
    db_util.run_statement(statement)
    statement = f'''
    ALTER TABLE {DB_SCHEMA}.map_layer ALTER COLUMN layer_workspace DROP NOT NULL;'''
    db_util.run_statement(statement)
    statement = f'''
    ALTER TABLE {DB_SCHEMA}.map_layer ALTER COLUMN layer_name DROP NOT NULL;'''
    db_util.run_statement(statement)


def adjust_db_for_created_at():
    logger.info(f'    Alter DB prime schema for storing created_at')
    statement = f'ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP;'
    db_util.run_statement(statement)


def adjust_publications_created_at():
    alter_tabel = f'''ALTER TABLE {DB_SCHEMA}.publications ALTER COLUMN created_at  SET NOT NULL;'''
    db_util.run_statement(alter_tabel)


def adjust_map_layer_data():
    db_util.run_statement(f'''
    alter table {DB_SCHEMA}.map_layer
      DROP COLUMN layer_name,
      DROP COLUMN layer_workspace,
      ALTER COLUMN layer_uuid SET NOT NULL
      ;''')

    logger.info(f'    Adjust UUID of layers in map_layer table DONE')


def ensure_layers_db_schema():
    logger.info(f'    Ensure DB schema')
    statement = sql.SQL("""CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {user}""").format(
        schema=sql.Identifier(layer_db.LAYERS_SCHEMA),
        user=sql.Identifier(settings.LAYMAN_PG_USER),
    )
    db_util.run_statement(statement)


def ensure_gs_workspaces_and_stores():
    logger.info(f'    Ensure GS workspaces and data stores')
    all_gs_workspaces = gs_util.get_all_workspaces(auth=settings.LAYMAN_GS_AUTH)
    assert GEOSERVER_WFS_WORKSPACE not in all_gs_workspaces
    assert GEOSERVER_WMS_WORKSPACE not in all_gs_workspaces
    gs_util.ensure_workspace(GEOSERVER_WFS_WORKSPACE, auth=settings.LAYMAN_GS_AUTH)
    gs_util.ensure_workspace(GEOSERVER_WMS_WORKSPACE, auth=settings.LAYMAN_GS_AUTH)

    gs_util.ensure_db_store(GEOSERVER_WFS_WORKSPACE, db_schema=layer_db.LAYERS_SCHEMA, pg_conn=settings.PG_CONN,
                            name=DEFAULT_INTERNAL_DB_STORE, auth=settings.LAYMAN_GS_AUTH)
    gs_util.ensure_db_store(GEOSERVER_WMS_WORKSPACE, db_schema=layer_db.LAYERS_SCHEMA, pg_conn=settings.PG_CONN,
                            name=DEFAULT_INTERNAL_DB_STORE, auth=settings.LAYMAN_GS_AUTH)
