import re
from collections import defaultdict, namedtuple
import math
import os
import logging
import subprocess
from psycopg2 import sql
from psycopg2.errors import InsufficientPrivilege

from db import util as db_util
from layman.common.language import get_languages_iso639_2
from layman.http import LaymanError
from layman import settings
from layman.util import get_publication_info
from .. import LAYER_TYPE, ATTRNAME_PATTERN

FLASK_CONN_CUR_KEY = f'{__name__}:CONN_CUR'
logger = logging.getLogger(__name__)

ColumnInfo = namedtuple('ColumnInfo', 'name data_type')


def get_internal_table_name(workspace, layer):
    layer_info = get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['uuid', 'original_data_source']})
    table_name = None
    if layer_info and layer_info['original_data_source'] == settings.EnumOriginalDataSource.FILE.value:
        uuid = layer_info['uuid'].replace('-', '_')
        table_name = f'layer_{uuid}'
    return table_name


def get_workspaces(conn_cur=None):
    """Returns workspaces from internal DB only"""
    if conn_cur is None:
        conn_cur = db_util.get_connection_cursor()
    _, cur = conn_cur

    query = sql.SQL("""select schema_name
    from information_schema.schemata
    where schema_name NOT IN ({schemas}) AND schema_owner = {layman_pg_user}""").format(
        schemas=sql.SQL(', ').join([sql.Literal(schema) for schema in settings.PG_NON_USER_SCHEMAS]),
        layman_pg_user=sql.Literal(settings.LAYMAN_PG_USER),
    )
    try:
        cur.execute(query)
    except BaseException as exc:
        logger.error(f'get_workspaces ERROR')
        raise LaymanError(7) from exc
    rows = cur.fetchall()
    return [
        r[0] for r in rows
    ]


def get_usernames():
    return []


def check_workspace_name(workspace):
    if workspace in settings.PG_NON_USER_SCHEMAS:
        raise LaymanError(35, {'reserved_by': __name__, 'schema': workspace})


def ensure_workspace(workspace, conn_cur=None):
    """Ensures workspace in internal DB only"""
    if conn_cur is None:
        conn_cur = db_util.get_connection_cursor()
    conn, cur = conn_cur

    statement = sql.SQL("""CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {user}""").format(
        schema=sql.Identifier(workspace),
        user=sql.Identifier(settings.LAYMAN_PG_USER),
    )
    try:
        cur.execute(statement)
        conn.commit()
    except BaseException as exc:
        logger.error(f'ensure_workspace ERROR')
        raise LaymanError(7) from exc


def delete_workspace(workspace, conn_cur=None):
    """Deletes workspace from internal DB only"""
    if conn_cur is None:
        conn_cur = db_util.get_connection_cursor()
    conn, cur = conn_cur

    statement = sql.SQL("""DROP SCHEMA IF EXISTS {schema} RESTRICT""").format(
        schema=sql.Identifier(workspace),
    )
    try:
        cur.execute(statement, (workspace, ))
        conn.commit()
    except BaseException as exc:
        logger.error(f'delete_workspace ERROR')
        raise LaymanError(7) from exc


def ensure_whole_user(username):
    """Ensures whole user in internal DB only"""
    ensure_workspace(username)


def delete_whole_user(username):
    """Deletes whole user from internal DB only"""
    delete_workspace(username)


def import_layer_vector_file_to_internal_table(workspace, layername, main_filepath, crs_id):
    table_name = get_internal_table_name(workspace, layername)
    assert table_name, f'workspace={workspace}, layername={layername}, table_name={table_name}'
    process = import_layer_vector_file_to_internal_table_async(workspace, table_name, main_filepath,
                                                               crs_id)
    while process.poll() is None:
        pass
    return_code = process.poll()
    if return_code != 0:
        pg_error = str(process.stdout.read())
        raise LaymanError(11, private_data=pg_error)


def create_ogr2ogr_args(*, schema, table_name, main_filepath, crs_id, output):
    pg_conn = ' '.join([f"{k}='{v}'" for k, v in settings.PG_CONN.items()])
    ogr2ogr_args = [
        'ogr2ogr',
        '-nln', table_name,
        '-nlt', 'GEOMETRY',
        '--config', 'OGR_ENABLE_PARTIAL_REPROJECTION', 'TRUE',
        '-lco', f'SCHEMA={schema}',
        # '-clipsrc', '-180', '-85.06', '180', '85.06',
        '-f', 'PostgreSQL',
        '-unsetFid',
        f'PG:{pg_conn}',
        # 'PG:{} active_schema={}'.format(PG_CONN, username),
    ]
    if crs_id is not None:
        ogr2ogr_args.extend([
            '-a_srs', crs_id,
        ])
    if os.path.splitext(main_filepath)[1] == '.shp':
        ogr2ogr_args.extend([
            '-lco', 'PRECISION=NO',
        ])
    ogr2ogr_args.extend([
        output,
    ])
    return ogr2ogr_args


def import_layer_vector_file_to_internal_table_async_with_iconv(schema, table_name, main_filepath, crs_id):
    assert table_name, f'schema={schema}, table_name={table_name}, main_filepath={main_filepath}'

    first_ogr2ogr_args = [
        'ogr2ogr',
        '--config', 'OGR_ENABLE_PARTIAL_REPROJECTION', 'TRUE',
        '-unsetFid',
        '-a_srs', crs_id,
        '-f', 'GeoJSON',
        '/vsistdout/',
        f'{main_filepath}',
    ]
    iconv_args = [
        'iconv',
        '-c',
        '-t', 'utf8',
    ]
    final_ogr2ogr_args = create_ogr2ogr_args(schema=schema,
                                             table_name=table_name,
                                             main_filepath=main_filepath,
                                             crs_id=crs_id,
                                             output='/vsistdin/')

    first_ogr2ogr_process = subprocess.Popen(first_ogr2ogr_args,
                                             stdout=subprocess.PIPE)
    with first_ogr2ogr_process.stdout:
        iconv_process = subprocess.Popen(iconv_args,
                                         stdin=first_ogr2ogr_process.stdout,
                                         stdout=subprocess.PIPE)
        with iconv_process.stdout:
            final_ogr2ogr_process = subprocess.Popen(final_ogr2ogr_args,
                                                     stdin=iconv_process.stdout,
                                                     stdout=subprocess.PIPE)
    return [first_ogr2ogr_process, iconv_process, final_ogr2ogr_process]


def import_layer_vector_file_to_internal_table_async(schema, table_name, main_filepath,
                                                     crs_id):
    # import file to database table
    assert table_name, f'schema={schema}, table_name={table_name}, main_filepath={main_filepath}'
    bash_args = create_ogr2ogr_args(schema=schema,
                                    table_name=table_name,
                                    main_filepath=main_filepath,
                                    crs_id=crs_id,
                                    output=main_filepath)

    # print(' '.join(bash_args))
    process = subprocess.Popen(bash_args, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    return process


def get_text_column_names(schema, table_name, conn_cur=None):
    _, cur = conn_cur or db_util.get_connection_cursor()

    statement = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = %s
AND table_name = %s
AND data_type IN ('character varying', 'varchar', 'character', 'char', 'text')
"""
    try:
        cur.execute(statement, (schema, table_name))
    except BaseException as exc:
        logger.error(f'get_text_column_names ERROR')
        raise LaymanError(7) from exc
    rows = cur.fetchall()
    return [r[0] for r in rows]


def get_internal_table_all_column_names(workspace, layername, conn_cur=None):
    table_name = get_internal_table_name(workspace, layername)
    return get_all_table_column_names(workspace, table_name, conn_cur=conn_cur)


def get_all_table_column_names(schema, table_name, conn_cur=None):
    return [col.name for col in get_all_column_infos(schema, table_name, conn_cur=conn_cur)]


def get_all_column_infos(schema, table_name, *, conn_cur=None, omit_geometry_columns=False):
    _, cur = conn_cur or db_util.get_connection_cursor()
    query = """
SELECT inf.column_name, inf.data_type
FROM information_schema.columns inf
    left outer join public.geometry_columns gc
        on (inf.table_schema = gc.f_table_schema
                and inf.table_name = gc.f_table_name
                and inf.column_name = gc.f_geometry_column)
WHERE table_schema = %s
AND table_name = %s
"""
    if omit_geometry_columns:
        query += " AND gc.f_geometry_column is null"

    try:
        cur.execute(query, (schema, table_name))
    except BaseException as exc:
        logger.error(f'get_all_column_names ERROR')
        raise LaymanError(7) from exc
    rows = cur.fetchall()
    return [ColumnInfo(name=r[0], data_type=r[1]) for r in rows]


def get_number_of_features(schema, table_name, conn_cur=None):
    _, cur = conn_cur or db_util.get_connection_cursor()

    statement = sql.SQL("""
select count(*)
from {table}
""").format(
        table=sql.Identifier(schema, table_name),
    )
    try:
        cur.execute(statement)
    except BaseException as exc:
        logger.error(f'get_number_of_features ERROR')
        raise LaymanError(7) from exc
    rows = cur.fetchall()
    return rows[0][0]


def get_text_data(schema, table_name, primary_key, conn_cur=None):
    _, cur = conn_cur or db_util.get_connection_cursor()
    col_names = get_text_column_names(schema, table_name, conn_cur=conn_cur)
    if len(col_names) == 0:
        return [], 0
    num_features = get_number_of_features(schema, table_name, conn_cur=conn_cur)
    if num_features == 0:
        return [], 0
    limit = max(100, num_features // 10)
    statement = sql.SQL("""
select {fields}
from {table}
order by {primary_key}
limit {limit}
""").format(
        fields=sql.SQL(',').join([sql.Identifier(col) for col in col_names]),
        table=sql.Identifier(schema, table_name),
        primary_key=sql.Identifier(primary_key),
        limit=sql.Literal(limit),
    )
    try:
        cur.execute(statement)
    except BaseException as exc:
        logger.error(f'get_text_data ERROR')
        raise LaymanError(7) from exc
    rows = cur.fetchall()
    col_texts = defaultdict(list)
    for row in rows:
        for idx, col_name in enumerate(col_names):
            val = row[idx]
            if val is not None and len(val) > 0:
                col_texts[col_name].append(val)
    col_texts = [
        ' '.join(texts)
        for _, texts in col_texts.items()
    ]
    # print(f"result col_texts={col_texts}")
    return col_texts, limit


def get_text_languages(schema, table_name, primary_key, *, conn_cur=None):
    texts, num_rows = get_text_data(schema, table_name, primary_key, conn_cur)
    all_langs = set()
    for text in texts:
        # skip short texts
        if len(text) < num_rows:
            continue
        langs = get_languages_iso639_2(text)
        if langs:
            lang = langs[0]
            # print(f"text={t}\nlanguage={lang}")
            all_langs.add(lang)
    return sorted(list(all_langs))


def get_most_frequent_lower_distance_query(schema, table_name, primary_key, geometry_column):
    query = sql.SQL("""
with t1 as (
select
  row_number() over (partition by {primary_key}) AS dump_id,
  sub_view.*
from (
  SELECT
    {primary_key}, (st_dump({geometry_column})).geom as geometry
  FROM {table}
) sub_view
order by ST_NPoints(geometry), {primary_key}, dump_id
limit 5000
)
, t2 as (
select
  row_number() over (partition by {primary_key}, dump_id) AS ring_id,
  sub_view.*
from (
(
   SELECT
    dump_id, {primary_key}, ST_ExteriorRing((ST_DumpRings(geometry)).geom) as geometry
  FROM t1
    where st_geometrytype(geometry) = 'ST_Polygon'
) union all (
   SELECT
    dump_id, {primary_key}, geometry
  FROM t1
    where st_geometrytype(geometry) = 'ST_LineString'
)
) sub_view
order by ST_NPoints(geometry), {primary_key}, dump_id, ring_id
limit 5000
)
, t2cumsum as (
select *, --ST_NPoints(geometry),
  sum(ST_NPoints(geometry)) over (order by ST_NPoints(geometry), {primary_key}, dump_id, ring_id
                                  rows between unbounded preceding and current row) as cum_sum_points
from t2
)
, t3 as (
SELECT {primary_key}, dump_id, ring_id, (ST_DumpPoints(st_transform(geometry, 4326))).*
FROM t2cumsum
where cum_sum_points < 50000
)
, t4 as MATERIALIZED (
    select t3.{primary_key}, t3.dump_id, t3.ring_id, t3.path[1] as point_idx, t3.geom as point1, t3p2.geom as point2
    from t3
             inner join t3 t3p2 on (t3.{primary_key} = t3p2.{primary_key} and
                                    t3.dump_id = t3p2.dump_id and
                                    t3.ring_id = t3p2.ring_id and
                                    t3.path[1] + 1 = t3p2.path[1])
)
, tdist as (
SELECT {primary_key}, dump_id, ring_id, point_idx,
    ST_DistanceSphere(point1, point2) as distance
FROM t4
)
, tstat as (
select
count(*) as num_distances,
percentile_disc(0.1) within group (order by tdist.distance) as p10
, percentile_disc(0.5) within group (order by tdist.distance) as p50
--, percentile_disc(0.9) within group (order by tdist.distance) as p90
from tdist
)
, tbounds as (
select
    --tstat.*,
    ((p50-p10)/10)*tmode.idx+p10 as lower_bound
    , ((p50-p10)/10)*(tmode.idx+0.5)+p10 as middle
    , ((p50-p10)/10)*(tmode.idx+1)+p10 as upper_bound
from tstat, (
    select generate_series(0, 9) as idx
) tmode
order by middle
)
, tfreq as (
select count(*) as freq, tbounds.middle
from tdist
inner join tbounds on (tdist.distance >= tbounds.lower_bound and tdist.distance < tbounds.upper_bound)
group by tbounds.middle
order by tbounds.middle
)
SELECT middle as distance, freq as distance_freq, tstat.num_distances
from tfreq, tstat
order by freq desc
limit 1
    """).format(
        table=sql.Identifier(schema, table_name),
        primary_key=sql.Identifier(primary_key),
        geometry_column=sql.Identifier(geometry_column),
    )
    return query


def get_most_frequent_lower_distance(schema, table_name, primary_key, geometry_column, conn_cur=None):
    _, cur = conn_cur or db_util.get_connection_cursor()

    query = get_most_frequent_lower_distance_query(schema, table_name, primary_key, geometry_column)

    # print(f"\nget_most_frequent_lower_distance v1\nusername={username}, layername={layername}")
    # print(query)

    try:
        cur.execute(query)
    except BaseException as exc:
        logger.error(f'get_most_frequent_lower_distance ERROR')
        raise LaymanError(7) from exc
    rows = cur.fetchall()
    # for row in rows:
    #     print(f"row={row}")
    result = None
    if len(rows) > 0:
        distance, freq, num_distances = rows[0]
        if freq / num_distances > 0.03:
            result = distance
    return result


SCALE_DENOMINATORS = [
    5000,
    10000,
    25000,
    50000,
    100000,
    250000,
    500000,
    1000000,
    2500000,
    5000000,
    10000000,
    25000000,
    50000000,
    100000000,
]


def guess_scale_denominator(schema, table_name, primary_key, geometry_column, *, conn_cur=None):
    distance = get_most_frequent_lower_distance(schema, table_name, primary_key, geometry_column, conn_cur=conn_cur)
    log_sd_list = [math.log10(sd) for sd in SCALE_DENOMINATORS]
    if distance is not None:
        coef = 2000 if distance > 100 else 1000
        log_dist = math.log10(distance * coef)
        sd_log = min(log_sd_list, key=lambda x: abs(x - log_dist))
        sd_idx = log_sd_list.index(sd_log)
        scale_denominator = SCALE_DENOMINATORS[sd_idx]
    else:
        scale_denominator = None
    return scale_denominator


def create_string_attributes(attribute_tuples, conn_cur=None):
    _, cur = conn_cur or db_util.get_connection_cursor()
    query = sql.SQL('{alters} \n COMMIT;').format(
        alters=sql.SQL('\n').join(
            [sql.SQL("""ALTER TABLE {table} ADD COLUMN {fattrname} VARCHAR(1024);""").format(
                table=sql.Identifier(schema, table_name),
                fattrname=sql.Identifier(attrname),
            ) for schema, table_name, attrname in attribute_tuples]
        )
    )
    try:
        cur.execute(query)
    except InsufficientPrivilege as exc:
        raise LaymanError(7, data={
            'reason': 'Insufficient privilege',
        }, http_code=403) from exc
    except BaseException as exc:
        logger.error(f'create_string_attributes ERROR, type={type(exc)}')
        raise LaymanError(7) from exc


def get_missing_attributes(attribute_tuples, conn_cur=None):
    _, cur = conn_cur or db_util.get_connection_cursor()

    # Find all foursomes which do not already exist
    query = sql.SQL("""select attribs.*
from ({selects}) attribs left join
    information_schema.columns c on c.table_schema = attribs.schema_name
                                and c.table_name = attribs.table_name
                                and c.column_name = attribs.attr_name
where c.column_name is null""").format(
        selects=sql.SQL("\n union all\n").join([sql.SQL("select {schema} schema_name, {table} table_name, {attr} attr_name").format(
            schema=sql.Literal(schema),
            table=sql.Literal(table),
            attr=sql.Literal(attr),
        ) for schema, table, attr in attribute_tuples])
    )

    try:
        if attribute_tuples:
            cur.execute(query)
    except BaseException as exc:
        logger.error(f'get_missing_attributes ERROR')
        raise LaymanError(7) from exc

    missing_attributes = set()
    rows = cur.fetchall()
    for row in rows:
        missing_attributes.add((row[0],
                                row[1],
                                row[2]))
    return missing_attributes


def ensure_attributes(attribute_tuples, conn_cur):
    missing_attributes = get_missing_attributes(attribute_tuples, conn_cur)
    if missing_attributes:
        dangerous_attribute_names = {
            a for _, _, a in missing_attributes
            if not re.match(ATTRNAME_PATTERN, a)
        }
        if dangerous_attribute_names:
            raise LaymanError(2, {
                'expected': r'Attribute names matching regex ^[a-zA-Z_][a-zA-Z_0-9]*$',
                'found': sorted(dangerous_attribute_names),
            })
        create_string_attributes(missing_attributes, conn_cur)
    return missing_attributes


def get_bbox(schema, table_name, conn_cur=None, column=settings.OGR_DEFAULT_GEOMETRY_COLUMN):
    query = sql.SQL('''
    with tmp as (select ST_Extent(l.{column}) as bbox
                 from {table} l
    )
    select st_xmin(bbox),
           st_ymin(bbox),
           st_xmax(bbox),
           st_ymax(bbox)
    from tmp
    ''').format(
        table=sql.Identifier(schema, table_name),
        column=sql.Identifier(column),
    )
    result = db_util.run_query(query, conn_cur=conn_cur)[0]
    return result


def get_table_crs(schema, table_name, conn_cur=None, column=settings.OGR_DEFAULT_GEOMETRY_COLUMN, *, use_internal_srid):
    srid = get_column_srid(schema, table_name, column, conn_cur=conn_cur)
    crs = db_util.get_crs_from_srid(srid, conn_cur, use_internal_srid=use_internal_srid)
    return crs


def get_column_srid(schema, table, column, *, conn_cur=None):
    query = 'select Find_SRID(%s, %s, %s);'
    srid = db_util.run_query(query, (schema, table, column), conn_cur=conn_cur)[0][0]
    return srid


def get_geometry_types(schema, table_name, *, column_name=settings.OGR_DEFAULT_GEOMETRY_COLUMN, conn_cur=None):
    conn, cur = conn_cur or db_util.get_connection_cursor()
    query = sql.SQL("""
    select distinct ST_GeometryType({column}) as geometry_type_name
    from {table}
    """).format(
        table=sql.Identifier(schema, table_name),
        column=sql.Identifier(column_name),
    )
    try:
        cur.execute(query)
    except BaseException as exc:
        logger.error(f'get_geometry_types ERROR')
        raise LaymanError(7) from exc
    rows = cur.fetchall()
    conn.commit()
    result = [row[0] for row in rows]
    return result
