import logging
from psycopg2 import sql

import requests_util.url_util
from db import util as db_util
from layman import settings, patch_mode, util as layman_util
from layman.common import empty_method, empty_method_returns_dict
from layman.http import LaymanError
from .. import LAYER_TYPE
from ..layer_class import Layer

logger = logging.getLogger(__name__)
PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_metadata_comparison = empty_method_returns_dict


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
                    'external_uri': requests_util.url_util.redact_uri(table_uri.db_uri_str),
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
                result['db']['external_uri'] = requests_util.url_util.redact_uri(table_uri.db_uri_str)
        elif layer_info['original_data_source'] == settings.EnumOriginalDataSource.TABLE.value:
            result['db'] = {
                'schema': table_uri.schema,
                'table': table_uri.table,
                'geo_column': table_uri.geo_column,
                'external_uri': requests_util.url_util.redact_uri(table_uri.db_uri_str),
                'status': 'NOT_AVAILABLE',
                'error': 'Table does not exist.',
            }

    return result


def delete_layer(workspace, layername):
    layer = Layer(layer_tuple=(workspace, layername))
    delete_layer_by_class(layer=layer)


def delete_layer_by_class(*, layer: Layer):
    """Deletes table from internal DB only"""
    query = sql.SQL("""
    DROP TABLE IF EXISTS {table} CASCADE
    """).format(
        table=sql.Identifier(layer.internal_db_names.schema, layer.internal_db_names.table),
    )
    try:
        db_util.run_statement(query)
    except BaseException as exc:
        raise LaymanError(7)from exc


def set_internal_table_layer_srid(schema, table_name, srid, ):
    query = '''SELECT UpdateGeometrySRID(%s, %s, %s, %s);'''
    params = (schema, table_name, settings.OGR_DEFAULT_GEOMETRY_COLUMN, srid)
    db_util.run_query(query, params)
