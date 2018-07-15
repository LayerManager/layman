import os
import re
import pathlib

from flask import Flask, request, redirect, jsonify
from osgeo import ogr

from .http import error
from .settings import *
from .util import to_safe_layer_name, get_main_file_name, get_file_name_mappings

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

@app.route('/')
def index():
    return redirect('/static/index.html')

@app.route('/layers', methods=['POST'])
def upload_file():
    app.logger.info('upload_file')

    # user
    if 'user' not in request.form:
        return error(1, {'parameter': 'user'})

    username = request.form['user']
    username_re = r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"
    if not re.match(username_re, username):
        return error(2, {'parameter': 'user', 'expected': username_re})

    if username in PG_NON_USER_SCHEMAS:
        return error(8, {'schema': username})

    # DB schema name conflicts
    import psycopg2
    try:
        conn = psycopg2.connect(PG_CONN)
    except:
        return error(6)
    cur = conn.cursor()
    try:
        cur.execute("""select catalog_name, schema_name, schema_owner
from information_schema.schemata
where schema_owner <> '{}' and schema_name = '{}'""".format(
            LAYMAN_PG_USER, username))
    except:
        return error(7)
    rows = cur.fetchall()
    if len(rows)>0:
        return error(10, {'schema': username})

    # user
    try:
        cur.execute("""CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}""".format(
        username, LAYMAN_PG_USER))
        conn.commit()
    except:
        return error(7)
    userdir = os.path.join(LAYMAN_DATA_PATH, username)
    pathlib.Path(userdir).mkdir(exist_ok=True)

    # file names
    if 'file' not in request.files:
        return error(1, {'parameter': 'file'})
    files = request.files.getlist("file")
    filenames = list(map(lambda f: f.filename, files))
    main_filename = get_main_file_name(filenames)
    if main_filename is None:
        return error(2, {'parameter': 'file', 'expected': \
            'At least one file with any of extensions: '+\
            ', '.join(MAIN_FILE_EXTENSIONS)})

    # name
    if 'name' in request.form and len(request.form['name']) > 0:
        layername = request.form['name']
    else:
        layername = os.path.splitext(main_filename)[0]
    layername = to_safe_layer_name(layername)

    # CRS 1/2
    crs_id = None
    if 'crs' in request.form:
        crs_id = request.form['crs']
        if crs_id not in INPUT_SRS_LIST:
            return error(2, {'parameter': 'crs', 'supported_values':
                INPUT_SRS_LIST})

    # file name conflicts
    filename_mapping, filepath_mapping = get_file_name_mappings(
        filenames, main_filename, layername, userdir
    )
    conflict_paths = [filename_mapping[k]
                      for k, v in filepath_mapping.items()
                      if v is not None and os.path.isfile(v)]
    if len(conflict_paths) > 0:
        return error(3, conflict_paths)

    # DB table name conflicts
    try:
        cur.execute("""SELECT n.nspname AS schemaname, c.relname, c.relkind
FROM   pg_class c
JOIN   pg_namespace n ON n.oid = c.relnamespace
WHERE  n.nspname IN ('{}', '{}') AND c.relname='{}'""".format(
            username, PG_POSTGIS_SCHEMA, layername))
    except:
        return error(7)
    rows = cur.fetchall()
    if len(rows)>0:
        return error(9, {'db_object_name': layername})

    # file saving
    for file in files:
        if filepath_mapping[file.filename] is None:
            continue
        app.logger.info('Saving file {} as {}'.format(
            file.filename, filepath_mapping[file.filename]))
        file.save(filepath_mapping[file.filename])
    n_uploaded_files = len({k:v
                            for k, v in filepath_mapping.items()
                            if v is not None})

    # feature layer
    inDriver = ogr.GetDriverByName("GeoJSON")
    inDataSource = inDriver.Open(filepath_mapping[main_filename], 0)
    n_layers = inDataSource.GetLayerCount()
    if n_layers != 1:
        return error(5, {'found': n_layers, 'expected': 1})
    feature_layer = inDataSource.GetLayerByIndex(0)
    # feature_layer.GetName()

    # CRS 2/2
    if crs_id is None:
        crs = feature_layer.GetSpatialRef()
        crs_auth_name = crs.GetAuthorityName(None)
        crs_code = crs.GetAuthorityCode(None)
        crs_id = crs_auth_name+":"+crs_code
        if crs_id not in INPUT_SRS_LIST:
            return error(4, {'found': crs_id, 'supported_values': INPUT_SRS_LIST})

    import subprocess
    bash_args = [
        'ogr2ogr',
        '-t_srs', 'EPSG:3857',
        '-s_srs', crs_id,
        '-nln', layername,
        '--config', 'OGR_ENABLE_PARTIAL_REPROJECTION', 'TRUE',
        '-lco', 'SCHEMA={}'.format(username),
        '-f', 'PostgreSQL',
        'PG:{}'.format(PG_CONN),
        # 'PG:{} active_schema={}'.format(PG_CONN, username),
        '{}'.format(filepath_mapping[main_filename]),
    ]
    # print('bash_args', ' '.join(bash_args))
    return_code = subprocess.call(bash_args)
    if return_code != 0:
        return error(11)


    return jsonify({
        'file_name': filename_mapping[main_filename],
        'table_name': layername,
        'layer_name': '{}:{}'.format(username, layername),
    }), 200
