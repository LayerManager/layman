import logging
from psycopg2 import sql

from db import util as db_util
from layman import settings, patch_mode, util as layman_util
from layman.common import empty_method, empty_method_returns_none, empty_method_returns_dict
from layman.http import LaymanError
from . import get_internal_table_name
from .. import LAYER_TYPE, util as layer_util

logger = logging.getLogger(__name__)
PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_metadata_comparison = empty_method_returns_dict
get_publication_uuid = empty_method_returns_none


def get_layer_info(workspace, layername,):
    layer_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['table_uri', 'original_data_source']})
    table_uri = layer_info.get('_table_uri')
    result = {}
    if table_uri:
        if layer_info['original_data_source'] == settings.EnumOriginalDataSource.FILE.value:
            db_uri_str = None
        else:
            db_uri_str = table_uri.db_uri_str
            try:
                db_util.get_connection_pool(db_uri_str=db_uri_str,)
            except BaseException:
                result['db'] = {
                    'schema': table_uri.schema,
                    'table': table_uri.table,
                    'geo_column': table_uri.geo_column,
                    'external_uri': layer_util.redact_uri(table_uri.db_uri_str),
                    'status': 'NOT_AVAILABLE',
                    'error': 'Cannot connect to DB.',
                }
                return result
        try:
            rows = db_util.run_query(f"""
    SELECT schemaname, tablename, tableowner
    FROM pg_tables
    WHERE schemaname = %s
        AND tablename = %s
    """, (table_uri.schema, table_uri.table, ), uri_str=db_uri_str)
        except BaseException as exc:
            raise LaymanError(7) from exc
        if len(rows) > 0:
            result['db'] = {
                'schema': table_uri.schema,
                'table': table_uri.table,
                'geo_column': table_uri.geo_column,
            }
            if layer_info['original_data_source'] == settings.EnumOriginalDataSource.TABLE.value:
                result['db']['external_uri'] = layer_util.redact_uri(table_uri.db_uri_str)
        elif layer_info['original_data_source'] == settings.EnumOriginalDataSource.TABLE.value:
            result['db'] = {
                'schema': table_uri.schema,
                'table': table_uri.table,
                'geo_column': table_uri.geo_column,
                'external_uri': layer_util.redact_uri(table_uri.db_uri_str),
                'status': 'NOT_AVAILABLE',
                'error': 'Table does not exist.',
            }

    return result


def delete_layer(workspace, layername, ):
    """Deletes table from internal DB only"""
    table_name = get_internal_table_name(workspace, layername)
    if table_name:
        query = sql.SQL("""
        DROP TABLE IF EXISTS {table} CASCADE
        """).format(
            table=sql.Identifier(workspace, table_name),
        )
        try:
            db_util.run_statement(query)
        except BaseException as exc:
            raise LaymanError(7)from exc


def set_internal_table_layer_srid(schema, table_name, srid, ):
    query = '''SELECT UpdateGeometrySRID(%s, %s, %s, %s);'''
    params = (schema, table_name, settings.OGR_DEFAULT_GEOMETRY_COLUMN, srid)
    db_util.run_query(query, params)
