from functools import wraps, partial
from urllib import parse
import re
import logging
import psycopg2

from flask import current_app, request
from db import TableUri, util as db_util
from layman import LaymanError, patch_mode, util as layman_util, settings
from layman.util import call_modules_fn, get_providers_from_source_names, get_internal_sources, \
    to_safe_name, url_for
from layman import celery as celery_util, common
from layman.common import redis as redis_util, tasks as tasks_util, metadata as metadata_common
from layman.common.prime_db_schema import publications
from layman.common.util import clear_publication_info as common_clear_publication_info
from . import get_layer_sources, LAYER_TYPE, get_layer_type_def, get_layer_info_keys, LAYERNAME_PATTERN, \
    LAYERNAME_MAX_LENGTH, SAFE_PG_IDENTIFIER_PATTERN
from .db import get_all_table_column_names, get_table_crs
from .layer_class import Layer
from ..uuid import delete_publication_uuid_from_redis

FLASK_PROVIDERS_KEY = f'{__name__}:PROVIDERS'
FLASK_SOURCES_KEY = f'{__name__}:SOURCES'

EXTERNAL_TABLE_URI_PATTERN = 'postgresql://<username>:<password>@<host>:<port>/<dbname>?schema=<schema_name>&table=<table_name>&geo_column=<geo_column_name>'
logger = logging.getLogger(__name__)


def to_safe_layer_name(value):
    return to_safe_name(value, 'layer')


def check_layername_decorator(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        check_layername(request.view_args['layername'])
        result = func(*args, **kwargs)
        return result

    return decorated_function


def check_layername(layername):
    if not re.match(LAYERNAME_PATTERN, layername):
        raise LaymanError(2, {'parameter': 'layername', 'expected': LAYERNAME_PATTERN})
    if len(layername) > LAYERNAME_MAX_LENGTH:
        raise LaymanError(2, {'parameter': 'layername',
                              'detail': f'Layer name too long ({len(layername)}), maximum allowed length is {LAYERNAME_MAX_LENGTH}.'})


def get_sources():
    key = FLASK_SOURCES_KEY
    if key not in current_app.config:
        current_app.config[key] = get_internal_sources(LAYER_TYPE)
    return current_app.config[key]


def get_providers():
    key = FLASK_PROVIDERS_KEY
    if key not in current_app.config:
        current_app.config[key] = get_providers_from_source_names(get_layer_sources())
    return current_app.config[key]


def fill_in_partial_info_statuses(info, chain_info):
    geodata_type = info.get('_file', {}).get('file_type') or info['geodata_type']
    original_data_source = info.get('original_data_source', settings.EnumOriginalDataSource.FILE.value)
    item_keys = get_layer_info_keys(geodata_type=geodata_type, original_data_source=original_data_source)

    return layman_util.get_info_with_statuses(info, chain_info, TASKS_TO_LAYER_INFO_KEYS, item_keys)


def get_layer_info(workspace, layername, context=None):
    partial_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context)

    chain_info = get_layer_chain(workspace, layername)

    filled_partial_info = fill_in_partial_info_statuses(partial_info, chain_info)
    return filled_partial_info


def clear_publication_info(layer_info, file_type):
    clear_info = common_clear_publication_info(layer_info)
    if file_type != settings.GEODATA_TYPE_RASTER:
        clear_info.pop('image_mosaic')
    return clear_info


def _get_complete_layer_info(workspace, layername, *, x_forwarded_items=None):
    partial_info = get_layer_info(workspace, layername, context={'x_forwarded_items': x_forwarded_items})

    if not any(partial_info):
        raise LaymanError(15, {'layername': layername})

    geodata_type = partial_info['geodata_type']
    original_data_source = partial_info['original_data_source']
    item_keys = get_layer_info_keys(geodata_type=geodata_type, original_data_source=original_data_source)

    complete_info = {}
    for key in item_keys:
        complete_info[key] = {'status': 'NOT_AVAILABLE'}

    complete_info.update({
        'name': layername,
        'url': url_for('rest_workspace_layer.get', layername=layername, workspace=workspace, x_forwarded_items=x_forwarded_items),
        'title': layername,
        'description': '',
    })

    complete_info.update(partial_info)
    file_type = complete_info.get('_file', {}).get('file_type')
    if complete_info['geodata_type'] == settings.GEODATA_TYPE_UNKNOWN and file_type and file_type != settings.GEODATA_TYPE_UNKNOWN:
        complete_info['geodata_type'] = file_type

    complete_info = clear_publication_info(complete_info, geodata_type)

    complete_info.pop('layman_metadata')
    complete_info['layman_metadata'] = {'publication_status': layman_util.get_publication_status(workspace, LAYER_TYPE, layername,
                                                                                                 complete_info, item_keys)}
    return complete_info


def get_complete_layer_info(workspace, layername, *, x_forwarded_items=None):
    return layman_util.get_complete_publication_info(workspace, LAYER_TYPE, layername,
                                                     x_forwarded_items=x_forwarded_items,
                                                     complete_info_method=_get_complete_layer_info)


def pre_publication_action_check(workspace, layername, task_options):
    # sync processing
    sources = get_sources()
    call_modules_fn(sources, 'pre_publication_action_check', [workspace, layername], kwargs=task_options)


def post_layer(workspace, layername, task_options, start_async_at):
    # sync processing
    sources = get_sources()
    call_modules_fn(sources, 'post_layer', [workspace, layername], kwargs=task_options)

    post_tasks = tasks_util.get_task_methods(get_layer_type_def(), workspace, layername, task_options, start_async_at)
    post_chain = tasks_util.get_chain_of_methods(workspace, layername, post_tasks, task_options, 'layername')
    # res = post_chain.apply_async()
    res = post_chain()

    celery_util.set_publication_chain_info(workspace, LAYER_TYPE, layername, post_tasks, res)


def patch_layer(layer: Layer, task_options, stop_sync_at, start_async_at):
    # sync processing
    sources = get_sources()
    stop_idx = next((idx for idx, s in enumerate(sources) if s.__name__ == stop_sync_at), len(sources))
    sources = sources[:stop_idx]
    call_modules_fn(sources, 'patch_layer', [layer.workspace, layer.name], kwargs=task_options)

    patch_tasks = tasks_util.get_task_methods(get_layer_type_def(), layer.workspace, layer.name, task_options, start_async_at)
    patch_chain = tasks_util.get_chain_of_methods(layer.workspace, layer.name, patch_tasks, task_options, 'layername')
    # res = patch_chain.apply_async()
    res = patch_chain()

    celery_util.set_publication_chain_info(layer.workspace, LAYER_TYPE, layer.name, patch_tasks, res)


TASKS_TO_LAYER_INFO_KEYS = {
    'layman.layer.filesystem.input_chunk.refresh': ['file'],
    'layman.layer.filesystem.gdal.refresh': ['file'],
    'layman.layer.db.table.refresh': ['db'],
    'layman.layer.geoserver.wfs.refresh': ['wfs'],
    'layman.layer.geoserver.wms.refresh': ['wms'],
    'layman.layer.geoserver.sld.refresh': ['style'],
    'layman.layer.filesystem.thumbnail.refresh': ['thumbnail'],
    'layman.layer.micka.soap.refresh': ['metadata'],
}


def patch_after_feature_change(workspace, layername, **kwargs):
    layman_util.patch_after_feature_change(workspace, LAYER_TYPE, layername, **kwargs)


def delete_layer_by_ws_name(workspace, layername, source=None, http_method='delete'):
    layer = Layer(layer_tuple=(workspace, layername))
    delete_layer(layer, source=source, http_method=http_method)


def delete_layer(layer: Layer, source=None, http_method='delete'):
    sources = get_sources()
    source_idx = next((
        idx for idx, m in enumerate(sources) if m.__name__ == source
    ), 0)
    end_idx = None if source_idx == 0 else source_idx - 1
    sources = sources[:end_idx:-1]
    if http_method == common.REQUEST_METHOD_PATCH:
        sources = [
            m for m in sources
            if m.PATCH_MODE == patch_mode.DELETE_IF_DEPENDANT
        ]
    # print(f"delete_layer {username}.{layername} using {len(sources)} sources: {[s.__name__ for s in sources]}")

    result = {}
    results = call_modules_fn(sources, 'delete_layer', [layer])
    for partial_result in results.values():
        if partial_result is not None:
            result.update(partial_result)
    if source is None:
        delete_publication_uuid_from_redis(layer.workspace, layer.type, layer.name, layer.uuid)
    celery_util.delete_publication(layer.workspace, layer.type, layer.name)
    return result


def get_layer_chain(workspace, layername):
    chain_info = celery_util.get_publication_chain_info(workspace, LAYER_TYPE, layername)
    return chain_info


def abort_layer_chain(workspace, layername):
    celery_util.abort_publication_chain(workspace, LAYER_TYPE, layername)


def is_layer_chain_ready(workspace, layername):
    chain_info = get_layer_chain(workspace, layername)
    return chain_info is None or celery_util.is_chain_ready(chain_info)


lock_decorator = redis_util.create_lock_decorator(LAYER_TYPE, 'layername', is_layer_chain_ready)


def layer_info_to_metadata_properties(info):
    result = {
        'title': info['title'],
        'identifier': {
            'identifier': info['url'],
            'label': info['name'],
        },
        'abstract': info['description'],
        'graphic_url': info.get('thumbnail', {}).get('url', None),
        'wms_url': info.get('wms', {}).get('url', None),
        'wfs_url': info.get('wfs', {}).get('url', None),
        'layer_endpoint': info['url'],
        'temporal_extent': info.get('wms', {}).get('time', {}).get('values'),
    }
    return result


def get_metadata_comparison(publication: Layer):
    layman_info = get_complete_layer_info(publication.workspace, publication.name)
    layman_props = layer_info_to_metadata_properties(layman_info)
    all_props = {
        f"{layman_props['layer_endpoint']}": layman_props,
    }
    sources = get_sources()
    partial_infos = call_modules_fn(sources, 'get_metadata_comparison', [publication])
    for partial_info in partial_infos.values():
        if partial_info is not None:
            all_props.update(partial_info)

    return metadata_common.transform_metadata_props_to_comparison(all_props)


get_syncable_prop_names = partial(metadata_common.get_syncable_prop_names, LAYER_TYPE)


def get_same_or_missing_prop_names(layer: Layer):
    md_comparison = get_metadata_comparison(layer)
    prop_names = get_syncable_prop_names()
    return metadata_common.get_same_or_missing_prop_names(prop_names, md_comparison)


def parse_and_validate_external_table_uri_str(external_table_uri_str):
    external_table_uri = parse.urlparse(external_table_uri_str, )
    if external_table_uri.scheme not in {'postgresql', 'postgres'}:
        raise LaymanError(2, {
            'parameter': 'external_table_uri',
            'message': 'Parameter `external_table_uri` is expected to have URI scheme `postgresql`',
            'expected': EXTERNAL_TABLE_URI_PATTERN,
            'found': {
                'external_table_uri': external_table_uri_str,
                'uri_scheme': external_table_uri.scheme,
            }
        })

    query = parse.parse_qs(external_table_uri.query)
    schema = query.pop('schema', [None])[0]
    table = query.pop('table', [None])[0]
    geo_column = query.pop('geo_column', [None])[0]
    db_uri = external_table_uri._replace(query=parse.urlencode(query, True))
    db_uri_str = parse.urlunparse(db_uri)
    if not all([schema, table, db_uri.hostname]):
        raise LaymanError(2, {
            'parameter': 'external_table_uri',
            'message': 'Parameter `external_table_uri` is expected to be valid URL with `host` part and query parameters `schema`, `table`, and `geo_column`.',
            'expected': EXTERNAL_TABLE_URI_PATTERN,
            'found': {
                'external_table_uri': external_table_uri_str,
                'host': db_uri.hostname,
                'schema': schema,
                'table': table,
                'geo_column': geo_column,
            }
        })

    try:
        db_util.get_connection_pool(db_uri_str=db_uri_str, encapsulate_exception=False)
    except psycopg2.OperationalError as exc:
        raise LaymanError(2, {
            'parameter': 'external_table_uri',
            'message': 'Unable to connect to database. Please check connection string, firewall settings, etc.',
            'expected': EXTERNAL_TABLE_URI_PATTERN,
            'detail': str(exc),
            'found': {
                'external_table_uri': external_table_uri_str,
            },
        }) from exc

    if not geo_column:
        query = f'''select f_geometry_column from geometry_columns where f_table_schema = %s and f_table_name = %s order by f_geometry_column asc'''
        query_res = db_util.run_query(query, (schema, table), uri_str=db_uri_str, )
        if len(query_res) == 0:
            raise LaymanError(2, {
                'parameter': 'external_table_uri',
                'message': 'Geometry column not found.',
                'expected': 'Table with at least one geometry column.',
                'found': {
                    'external_table_uri': external_table_uri_str,
                    'schema': schema,
                    'table': table,
                }
            })
        geo_column = query_res[0][0]

    for name in [schema, table, geo_column]:
        if not re.match(SAFE_PG_IDENTIFIER_PATTERN, name):
            raise LaymanError(2, {
                'parameter': 'external_table_uri',
                'message': 'Schema, table, and geo_column in `external_table_uri` parameter are expected to match regular expression ' + SAFE_PG_IDENTIFIER_PATTERN,
                'found': {
                    'external_table_uri': external_table_uri_str,
                    'schema': schema,
                    'table': table,
                    'geo_column': geo_column,
                }
            })

    query = f'''select count(*) from information_schema.tables WHERE table_schema=%s and table_name=%s'''
    query_res = db_util.run_query(query, (schema, table,), uri_str=db_uri_str, )
    if not query_res[0][0]:
        query = f'''select table_schema, table_name from information_schema.tables WHERE lower(table_schema)=lower(%s) and lower(table_name)=lower(%s)'''
        query_res = db_util.run_query(query, (schema, table,), uri_str=db_uri_str, )
        suggestion = f" Did you mean \"{query_res[0][0]}\".\"{query_res[0][1]}\"?" if query_res else ''
        raise LaymanError(2, {
            'parameter': 'external_table_uri',
            'message': f'Table "{schema}"."{table}" not found in database.{suggestion}',
            'expected': EXTERNAL_TABLE_URI_PATTERN,
            'found': {
                'external_table_uri': external_table_uri_str,
                'schema': schema,
                'table': table,
            }
        })

    query = f'''select count(*) from geometry_columns where f_table_schema = %s and f_table_name = %s and f_geometry_column = %s'''
    query_res = db_util.run_query(query, (schema, table, geo_column), uri_str=db_uri_str, )
    if not query_res[0][0]:
        raise LaymanError(2, {
            'parameter': 'external_table_uri',
            'message': 'Column `geo_column` not found among geometry columns.',
            'expected': EXTERNAL_TABLE_URI_PATTERN,
            'found': {
                'external_table_uri': external_table_uri_str,
                'schema': schema,
                'table': table,
                'geo_column': geo_column,
            }
        })

    crs = get_table_crs(schema, table, uri_str=db_uri_str, column=geo_column, use_internal_srid=False)
    if crs not in settings.INPUT_SRS_LIST:
        raise LaymanError(2, {
            'parameter': 'external_table_uri',
            'message': 'Unsupported CRS of table data.',
            'supported_values': settings.INPUT_SRS_LIST,
            'found': crs,
        })

    # https://stackoverflow.com/a/20537829
    query = '''
SELECT
  attr.attname,
  format_type(attr.atttypid, attr.atttypmod)
FROM pg_index idx inner join
     pg_attribute attr on attr.attnum = any(idx.indkey) inner join
     pg_class cls on idx.indrelid = cls.oid AND
                     cls.oid = attr.attrelid inner join
     pg_namespace nspace on nspace.oid = cls.relnamespace
WHERE
  idx.indisprimary AND
  cls.relname = %s AND
  nspace.nspname = %s'''
    query_res = db_util.run_query(query, (table, schema), uri_str=db_uri_str, log_query=True)
    primary_key_columns = [r[0] for r in query_res]
    if len(query_res) == 0:
        raise LaymanError(2, {
            'parameter': 'external_table_uri',
            'message': 'No primary key found in the table.',
            'expected': 'Table with one-column primary key.',
            'found': {
                'external_table_uri': external_table_uri_str,
                'schema': schema,
                'table': table,
                'primary_key_columns': primary_key_columns,
            }
        })
    if len(query_res) > 1:
        raise LaymanError(2, {
            'parameter': 'external_table_uri',
            'message': 'Table with multi-column primary key.',
            'expected': 'Table with one-column primary key.',
            'found': {
                'external_table_uri': external_table_uri_str,
                'schema': schema,
                'table': table,
                'primary_key_columns': primary_key_columns,
            }
        })

    column_names = get_all_table_column_names(schema, table, uri_str=db_uri_str)
    unsafe_column_names = [c for c in column_names if not re.match(SAFE_PG_IDENTIFIER_PATTERN, c)]
    if unsafe_column_names:
        raise LaymanError(2, {
            'parameter': 'external_table_uri',
            'message': 'Expected table with all column names matching regular expression ' + SAFE_PG_IDENTIFIER_PATTERN,
            'found': {
                'external_table_uri': external_table_uri_str,
                'schema': schema,
                'table': table,
                'unsafe_column_names': unsafe_column_names,
            }
        })

    result = TableUri(db_uri_str=db_uri_str,
                      schema=schema,
                      table=table,
                      geo_column=geo_column,
                      primary_key_column=primary_key_columns[0],
                      )

    return result


def set_wfs_wms_status_after_fail(workspace, name):
    keys = ['wfs', 'wms', 'style', 'geodata_type']
    publ_info = layman_util.get_publication_info(workspace, LAYER_TYPE, name, context={'keys': keys})
    keys.remove('geodata_type')
    if publ_info['geodata_type'] == settings.GEODATA_TYPE_RASTER:
        keys.remove('wfs')
    wfs_wms_status = settings.EnumWfsWmsStatus.AVAILABLE if all(
        publ_info.get(key) for key in keys) else settings.EnumWfsWmsStatus.NOT_AVAILABLE
    publications.set_wfs_wms_status(workspace, LAYER_TYPE, name, wfs_wms_status)
