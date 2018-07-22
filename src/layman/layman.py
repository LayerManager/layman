import os
import re
import pathlib
import json
import base64
from urllib.parse import urljoin, urlparse

from flask import Flask, request, redirect, jsonify
from osgeo import ogr

from .http import error
from .settings import *
from .util import to_safe_layer_name, get_main_file_name, \
    get_file_name_mappings, get_layman_rules, get_non_layman_workspaces

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

    # GeoServer workspace name conflicts
    if username in GS_RESERVED_WORKSPACE_NAMES:
        return error(13, {'workspace': username})
    import requests
    headers_json = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }
    headers_xml = {
        'Accept': 'application/xml',
        'Content-type': 'application/xml',
    }

    r = requests.get(
        LAYMAN_GS_REST_WORKSPACES,
        # data=json.dumps(payload),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    # app.logger.info(r.text)
    all_workspaces = r.json()['workspaces']['workspace']

    r = requests.get(
        LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
        # data=json.dumps(payload),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    # app.logger.info(r.text)
    all_rules = r.json()
    layman_rules = get_layman_rules(all_rules)
    non_layman_workspaces = get_non_layman_workspaces(all_workspaces,
                                                      layman_rules)

    if any(ws['name']==username for ws in non_layman_workspaces):
        return error(12, {'workspace': username})

    # user
    userdir = os.path.join(LAYMAN_DATA_PATH, username)
    pathlib.Path(userdir).mkdir(exist_ok=True)

    try:
        cur.execute("""CREATE SCHEMA IF NOT EXISTS "{}" AUTHORIZATION {}""".format(
        username, LAYMAN_PG_USER))
        conn.commit()
    except:
        return error(7)

    if not any(ws['name'] == username for ws in all_workspaces):
        r = requests.post(
            LAYMAN_GS_REST_WORKSPACES,
            data=json.dumps({'workspace': {'name': username}}),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        r = requests.post(
            LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
            data=json.dumps({username+'.*.r': LAYMAN_GS_ROLE+',ROLE_ANONYMOUS'}),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        r = requests.post(
            urljoin(LAYMAN_GS_REST_WORKSPACES, username+'/datastores'),
            data=json.dumps({
              "dataStore": {
                "name": "postgresql",
                "connectionParameters": {
                  "entry": [
                    {
                      "@key": "dbtype",
                      "$": "postgis"
                    },
                    {
                      "@key": "host",
                      "$": LAYMAN_PG_HOST
                    },
                    {
                      "@key": "port",
                      "$": LAYMAN_PG_PORT
                    },
                    {
                      "@key": "database",
                      "$": LAYMAN_PG_DBNAME
                    },
                    {
                      "@key": "user",
                      "$": LAYMAN_PG_USER
                    },
                    {
                      "@key": "passwd",
                      "$": LAYMAN_PG_PASSWORD
                    },
                    {
                      "@key": "schema",
                      "$": username
                    },
                  ]
                },
              }
            }),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()

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
    if len(request.form.get('name', '')) > 0:
        layername = request.form['name']
    else:
        layername = os.path.splitext(main_filename)[0]
    layername = to_safe_layer_name(layername)

    # CRS 1/2
    crs_id = None
    if len(request.form.get('crs', '')) > 0:
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

    # check feature layers in source file
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

    # import file to database table
    import subprocess
    bash_args = [
        'ogr2ogr',
        '-t_srs', 'EPSG:3857',
        '-s_srs', crs_id,
        '-nln', layername,
        '--config', 'OGR_ENABLE_PARTIAL_REPROJECTION', 'TRUE',
        '-lco', 'SCHEMA={}'.format(username),
        # '-clipsrc', '-180', '-85.06', '180', '85.06',
        '-f', 'PostgreSQL',
        'PG:{}'.format(PG_CONN),
        # 'PG:{} active_schema={}'.format(PG_CONN, username),
        '{}'.format(filepath_mapping[main_filename]),
    ]
    # app.logger.info(' '.join(bash_args))
    return_code = subprocess.call(bash_args)
    if return_code != 0:
        return error(11)

    # title and description
    if len(request.form.get('title', '')) > 0:
        title = request.form['title']
    else:
        title = layername
    description = request.form.get('description', '')

    # publish table as new layer
    keywords = [
        "features",
        layername,
        title
    ]
    keywords = list(set(keywords))
    r = requests.post(
        urljoin(LAYMAN_GS_REST_WORKSPACES,
                username+'/datastores/postgresql/featuretypes/'),
        data=json.dumps(
            {
                "featureType": {
                    "name": layername,
                    "title": title,
                    "abstract": description,
                    "keywords": {
                        "string": keywords
                    },
                    "srs": "EPSG:3857",
                    "projectionPolicy": "FORCE_DECLARED",
                    "enabled": True,
                    "store": {
                        "@class": "dataStore",
                        "name": username+":postgresql",
                    },
                }
            }
        ),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()

    # SLD
    if 'sld' in request.files:
        sld_file = request.files['sld']
        r = requests.post(
            urljoin(LAYMAN_GS_REST_WORKSPACES, username + '/styles/'),
            data=json.dumps(
                {
                    "style": {
                        "name": layername,
                        # "workspace": {
                        #     "name": "browser"
                        # },
                        "format": "sld",
                        # "languageVersion": {
                        #     "version": "1.0.0"
                        # },
                        "filename": layername+".sld"
                    }
                }
            ),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        # app.logger.info(sld_file.read())
        r = requests.put(
            urljoin(LAYMAN_GS_REST_WORKSPACES, username +
                    '/styles/'+layername),
            data=sld_file.read(),
            headers={
                'Accept': 'application/json',
                'Content-type': 'application/vnd.ogc.sld+xml',
            },
            auth=LAYMAN_GS_AUTH
        )
        if r.status_code == 400:
            return error(14, data=r.text)
        r.raise_for_status()
        r = requests.put(
            urljoin(LAYMAN_GS_REST_WORKSPACES, username +
                    '/layers/'+layername),
            data=json.dumps(
                {
                    "layer": {
                        "defaultStyle": {
                            "name": username + ':' + layername,
                            "workspace": username,
                        },
                    }
                }
            ),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH
        )
        # app.logger.info(r.text)
        r.raise_for_status()

    # generate thumbnail
    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    from .gs_util import wms_proxy
    wms = wms_proxy(wms_url)
    # app.logger.info(list(wms.contents))
    bbox = list(wms[layername].boundingBox)
    # app.logger.info(bbox)
    min_range = min(bbox[2]-bbox[0], bbox[3]-bbox[1]) / 2
    tn_bbox = (
        (bbox[0] + bbox[2]) / 2 - min_range,
        (bbox[1] + bbox[3]) / 2 - min_range,
        (bbox[0] + bbox[2]) / 2 + min_range,
        (bbox[1] + bbox[3]) / 2 + min_range,
    )
    tn_img = wms.getmap(
        layers=[layername],
        srs='EPSG:3857',
        bbox=tn_bbox,
        size=(300, 300),
        format='image/png',
        transparent=True,
    )
    tn_path = os.path.splitext(filepath_mapping[main_filename])[
                  0]+'.thumbnail.png'
    out = open(tn_path, 'wb')
    out.write(tn_img.read())
    out.close()

    # return result
    wms_proxy_url = urljoin(LAYMAN_GS_PROXY_URL, username + '/ows')
    wfs_proxy_url = wms_proxy_url

    return jsonify({
        'file_name': filename_mapping[main_filename],
        'table_name': layername,
        'layer_name': layername,
        'wms': wms_proxy_url,
        'wfs': wfs_proxy_url,
        'thumbnail': ("data:image/png;" +
                      "base64," + base64.b64encode(tn_img.read()).decode('utf-8')),
    }), 200
