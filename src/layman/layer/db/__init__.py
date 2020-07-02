from collections import defaultdict
import math
import os
import psycopg2
from flask import g

from layman.common.language import get_languages_iso639_2
from layman.http import LaymanError
from layman import settings

FLASK_CONN_CUR_KEY = f'{__name__}:CONN_CUR'


def create_connection_cursor():
    try:
        connection = psycopg2.connect(**settings.PG_CONN)
    except:
        raise LaymanError(6)
    cursor = connection.cursor()
    return (connection, cursor)


def get_connection_cursor():
    key = FLASK_CONN_CUR_KEY
    if key not in g:
        conn_cur = create_connection_cursor()
        g.setdefault(key, conn_cur)
    return g.get(key)


def get_usernames(conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute(f"""select schema_name
    from information_schema.schemata
    where schema_name NOT IN ('{"', '".join(settings.PG_NON_USER_SCHEMAS)}\
') AND schema_owner = '{settings.LAYMAN_PG_USER}'""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    return [
        r[0] for r in rows
    ]


def check_username(username, conn_cur=None):
    if username in settings.PG_NON_USER_SCHEMAS:
        raise LaymanError(35, {'reserved_by': __name__, 'schema': username})

    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute(f"""select catalog_name, schema_name, schema_owner
    from information_schema.schemata
    where schema_owner <> '{settings.LAYMAN_PG_USER}' and schema_name = '{username}'""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    if len(rows) > 0:
        raise LaymanError(35, {'reserved_by': __name__, 'schema': username,
                               'reason': 'DB schema owned by another than layman user'})


def ensure_user_workspace(username, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute(
            f"""CREATE SCHEMA IF NOT EXISTS "{username}" AUTHORIZATION {settings.LAYMAN_PG_USER}""")
        conn.commit()
    except:
        raise LaymanError(7)


def delete_user_workspace(username, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute(
            f"""DROP SCHEMA IF EXISTS "{username}" RESTRICT""")
        conn.commit()
    except:
        raise LaymanError(7)


# def import_layer_vector_file(username, layername, main):
def import_layer_vector_file(username, layername, main_filepath, crs_id):
    p = import_layer_vector_file_async(username, layername, main_filepath,
                                       crs_id)
    while p.poll() is None:
        pass
    return_code = p.poll()
    if return_code != 0:
        pg_error = str(p.stdout.read())
        raise LaymanError(11, private_data=pg_error)


def import_layer_vector_file_async(username, layername, main_filepath,
                                   crs_id):
    # import file to database table
    import subprocess
    pg_conn = ' '.join([f"{k}='{v}'" for k, v in settings.PG_CONN.items()])
    bash_args = [
        'ogr2ogr',
        '-t_srs', 'EPSG:3857',
        '-nln', layername,
        '--config', 'OGR_ENABLE_PARTIAL_REPROJECTION', 'TRUE',
        '-lco', f'SCHEMA={username}',
        # '-clipsrc', '-180', '-85.06', '180', '85.06',
        '-f', 'PostgreSQL',
        f'PG:{pg_conn}',
        # 'PG:{} active_schema={}'.format(PG_CONN, username),
    ]
    if crs_id is not None:
        bash_args.extend([
            '-s_srs', crs_id,
        ])
    if os.path.splitext(main_filepath)[1] == '.shp':
        bash_args.extend([
            '-nlt', 'PROMOTE_TO_MULTI',
            '-lco', 'PRECISION=NO',
        ])
    bash_args.extend([
        f'{main_filepath}',
    ])

    # print(' '.join(bash_args))
    p = subprocess.Popen(bash_args, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return p


def check_new_layername(username, layername, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    # DB table name conflicts
    try:
        cur.execute(f"""SELECT n.nspname AS schemaname, c.relname, c.relkind
    FROM   pg_class c
    JOIN   pg_namespace n ON n.oid = c.relnamespace
    WHERE  n.nspname IN ('{username}', '{settings.PG_POSTGIS_SCHEMA}') AND c.relname='{layername}'""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    if len(rows) > 0:
        raise LaymanError(9, {'db_object_name': layername})


def get_text_column_names(username, layername, conn_cur=None):
    conn, cur = conn_cur or get_connection_cursor()

    try:
        cur.execute(f"""
SELECT QUOTE_IDENT(column_name) AS column_name
FROM information_schema.columns 
WHERE table_schema = '{username}' 
AND table_name = '{layername}'
AND data_type IN ('character varying', 'varchar', 'character', 'char', 'text')
""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    return [r[0] for r in rows]


def get_number_of_features(username, layername, conn_cur=None):
    conn, cur = conn_cur or get_connection_cursor()

    try:
        cur.execute(f"""
select count(*)
from {username}.{layername}
""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    return rows[0][0]


def get_text_data(username, layername, conn_cur=None):
    conn, cur = conn_cur or get_connection_cursor()
    col_names = get_text_column_names(username, layername, conn_cur=conn_cur)
    if len(col_names) == 0:
        return None
    num_features = get_number_of_features(username, layername, conn_cur=conn_cur)
    if num_features == 0:
        return None
    limit = max(100, num_features // 10)
    try:
        cur.execute(f"""
select {', '.join(col_names)}
from {username}.{layername}
order by ogc_fid
limit {limit}
""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    col_texts = defaultdict(list)
    for row in rows:
        for idx in range(len(col_names)):
            col_name = col_names[idx]
            v = row[idx]
            if v is not None and len(v) > 0:
                col_texts[col_name].append(v)
    col_texts = [
        ' '.join(texts)
        for _, texts in col_texts.items()
    ]
    # print(f"result col_texts={col_texts}")
    return col_texts, limit


def get_text_languages(username, layername):
    texts, num_rows = get_text_data(username, layername)
    all_langs = set()
    for t in texts:
        # skip short texts
        if len(t) < num_rows:
            continue
        langs = get_languages_iso639_2(t)
        if len(langs):
            lang = langs[0]
            # print(f"text={t}\nlanguage={lang}")
            all_langs.add(lang)
    return sorted(list(all_langs))


def get_most_frequent_lower_distance(username, layername, conn_cur=None):
    conn, cur = conn_cur or get_connection_cursor()

    query = f"""
with t1 as (
select
  row_number() over (partition by ogc_fid) AS dump_id,
  sub_view.*
from (
  SELECT
    ogc_fid, (st_dump(wkb_geometry)).geom as geometry
  FROM {username}.{layername}
) sub_view
order by ST_NPoints(geometry), ogc_fid, dump_id
limit 5000
)
, t2 as (
select
  row_number() over (partition by ogc_fid, dump_id) AS ring_id,
  sub_view.*
from (
(
   SELECT
    dump_id, ogc_fid, ST_ExteriorRing((ST_DumpRings(geometry)).geom) as geometry
  FROM t1
    where st_geometrytype(geometry) = 'ST_Polygon'
) union all (
   SELECT
    dump_id, ogc_fid, geometry
  FROM t1
    where st_geometrytype(geometry) = 'ST_LineString'
)
) sub_view
order by ST_NPoints(geometry), ogc_fid, dump_id, ring_id
limit 5000
)
, t2cumsum as (
select *, --ST_NPoints(geometry),
  sum(ST_NPoints(geometry)) over (order by ST_NPoints(geometry), ogc_fid, dump_id, ring_id
                                  rows between unbounded preceding and current row) as cum_sum_points
from t2
)
, t3 as (
SELECT ogc_fid, dump_id, ring_id, geometry, generate_series(1, st_npoints(geometry)-1) as point_idx
FROM t2cumsum
where cum_sum_points < 50000
)
, tdist as (
SELECT ogc_fid, dump_id, ring_id, ST_PointN(geometry, point_idx), point_idx,
    st_distance(ST_PointN(geometry, point_idx), ST_PointN(geometry, point_idx+1)) as distance
FROM t3
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
        """

    # print(f"\nget_most_frequent_lower_distance v1\nusername={username}, layername={layername}")
    # print(query)

    try:
        cur.execute(query)
    except:
        raise LaymanError(7)
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


def guess_scale_denominator(username, layername):
    distance = get_most_frequent_lower_distance(username, layername)
    log_sd_list = [math.log10(sd) for sd in SCALE_DENOMINATORS]
    if distance is not None:
        coef = 2000 if distance > 100 else 1000
        log_dist = math.log10(distance * coef)
        sd_log = min(log_sd_list, key=lambda x: abs(x - log_dist))
        sd_idx = log_sd_list.index(sd_log)
        sd = SCALE_DENOMINATORS[sd_idx]
    else:
        sd = None
    return sd


def get_most_frequent_lower_distance2(username, layername, conn_cur=None):
    conn, cur = conn_cur or get_connection_cursor()

    query = f"""
with t1 as (
select
  row_number() over (partition by ogc_fid) AS dump_id,
  sub_view.*
from (
  SELECT
    ogc_fid, (st_dump(wkb_geometry)).geom as geometry
  FROM {username}.{layername}
) sub_view
order by st_area(Box2D(geometry)), ogc_fid, dump_id
limit 5000
)
, t2 as (
select
  row_number() over (partition by ogc_fid, dump_id) AS ring_id,
  sub_view.*
from (
(
   SELECT
    dump_id, ogc_fid, ST_ExteriorRing((ST_DumpRings(geometry)).geom) as geometry
  FROM t1
    where st_geometrytype(geometry) = 'ST_Polygon'
) union all (
   SELECT
    dump_id, ogc_fid, geometry
  FROM t1
    where st_geometrytype(geometry) = 'ST_LineString'
)
) sub_view
order by st_area(Box2D(geometry)), ogc_fid, dump_id, ring_id
limit 5000
)
, t2cumsum as (
select *, --ST_NPoints(geometry),
  sum(ST_NPoints(geometry)) over (order by ST_NPoints(geometry), ogc_fid, dump_id, ring_id
                                  rows between unbounded preceding and current row) as cum_sum_points
from t2
)
, t3 as (
SELECT ogc_fid, dump_id, ring_id, geometry, generate_series(1, st_npoints(geometry)-1) as point_idx
FROM t2cumsum
where cum_sum_points < 50000
)
, tdist as (
SELECT ogc_fid, dump_id, ring_id, ST_PointN(geometry, point_idx), point_idx,
    st_distance(ST_PointN(geometry, point_idx), ST_PointN(geometry, point_idx+1)) as distance
FROM t3
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
        """

    # print(f"\nget_most_frequent_lower_distance v2\nusername={username}, layername={layername}")
    # print(query)

    try:
        cur.execute(query)
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    # for row in rows:
    #     print(f"row={row}")
    result = None
    if len(rows) > 0:
        distance, freq, num_distances = rows[0]
        if freq / num_distances > 0.03:
            result = distance
    return result
