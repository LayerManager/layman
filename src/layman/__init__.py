import base64
import re

from flask import Flask, request, redirect, jsonify, url_for, send_file

from layman import db
from layman import filesystem
from layman.filesystem import thumbnail
from layman.filesystem import input_files
from layman import geoserver
from .util import to_safe_layer_name
from .http import LaymanError
from .settings import *

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

username_re = r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"
layername_re = username_re

@app.route('/')
def index():
    return redirect('/static/test-client/index.html')


@app.route('/rest/<username>/layers', methods=['GET'])
def get_layers(username):
    app.logger.info('GET Layers')

    # USER
    if not re.match(username_re, username):
        raise LaymanError(2, {'parameter': 'user', 'expected': username_re})
    if username in PG_NON_USER_SCHEMAS:
        raise LaymanError(8, {'schema': username})
    if username in GS_RESERVED_WORKSPACE_NAMES:
        raise LaymanError(13, {'workspace': username})

    layernames = \
        input_files.get_layer_names(username) \
        + db.get_layer_names(username) \
        + geoserver.get_layer_names(username)
    layernames = list(set(layernames))

    infos = list(map(
        lambda layername: {
            'name': layername,
            'url': url_for('get_layer', layername=layername, username=username)
        },
        layernames
    ))
    return jsonify(infos), 200


@app.route('/rest/<username>/layers', methods=['POST'])
def post_layers(username):
    app.logger.info('POST Layers')

    # USER
    if not re.match(username_re, username):
        raise LaymanError(2, {'parameter': 'user', 'expected': username_re})
    if username in PG_NON_USER_SCHEMAS:
        raise LaymanError(8, {'schema': username})
    if username in GS_RESERVED_WORKSPACE_NAMES:
        raise LaymanError(13, {'workspace': username})

    # FILE
    if 'file' not in request.files:
        raise LaymanError(1, {'parameter': 'file'})
    files = request.files.getlist("file")

    # NAME
    unsafe_layername = request.form.get('name', '')
    if len(unsafe_layername) == 0:
        unsafe_layername = input_files.get_unsafe_layername(files)
    layername = to_safe_layer_name(unsafe_layername)

    # CRS
    crs_id = None
    if len(request.form.get('crs', '')) > 0:
        crs_id = request.form['crs']
        if crs_id not in INPUT_SRS_LIST:
            raise LaymanError(2, {'parameter': 'crs', 'supported_values':
                INPUT_SRS_LIST})
    check_crs = crs_id is None

    # TITLE
    if len(request.form.get('title', '')) > 0:
        title = request.form['title']
    else:
        title = layername

    # DESCRIPTION
    description = request.form.get('description', '')

    # SLD
    sld_file = None
    if 'sld' in request.files:
        sld_file = request.files['sld']

    # save files
    userdir = filesystem.ensure_user_dir(username)
    main_filename = input_files.save_layer_files(username, layername, files)
    main_filepath = os.path.join(userdir, main_filename)
    if check_crs:
        input_files.check_layer_crs(main_filepath)

    # import into DB table
    db.ensure_user_schema(username)
    db.import_layer_vector_file(username, layername, main_filepath, crs_id)

    # publish layer to GeoServer
    geoserver.ensure_user_workspace(username)
    geoserver.publish_layer_from_db(username, layername, description, title,
                                    sld_file)

    # generate thumbnail
    geoserver.generate_layer_thumbnail(username, layername)

    layerurl = url_for('get_layer', layername=layername, username=username)

    app.logger.info('uploaded layer '+layername)
    return jsonify([{
        'name': layername,
        'url': layerurl,
    }]), 200


@app.route('/rest/<username>/layers/<layername>', methods=['GET'])
def get_layer(username, layername):
    app.logger.info('GET Layer')

    # USER
    if not re.match(username_re, username):
        raise LaymanError(2, {'parameter': 'user', 'expected': username_re})
    if username in PG_NON_USER_SCHEMAS:
        raise LaymanError(8, {'schema': username})
    if username in GS_RESERVED_WORKSPACE_NAMES:
        raise LaymanError(13, {'workspace': username})

    # LAYER
    if not re.match(layername_re, layername):
        raise LaymanError(2, {'parameter': 'layername', 'expected':
            layername_re})


    main_file_info = input_files.get_layer_info(username, layername)

    thumbnail_info = thumbnail.get_layer_info(username, layername)

    table_info = db.get_table_info(username, layername)

    layer_info = geoserver.get_layer_info(username, layername)

    infos = [
        main_file_info,
        thumbnail_info,
        table_info,
        layer_info,
    ]

    if not any(infos):
        raise LaymanError(15, {'layername': layername})

    complete_info = {
        'name': layername,
        'url': request.path,
        'title': layername,
        'description': '',
        'wms': {
            'status': 'not_available'
        },
        'wfs': {
            'status': 'not_available'
        },
        'thumbnail': {
            'status': 'not_available'
        },
        'file': {
            'status': 'not_available'
        },
        'db_table': {
            'status': 'not_available'
        },
    }

    for info in infos:
        complete_info.update(info)

    return jsonify(complete_info), 200


@app.route('/rest/<username>/layers/<layername>/thumbnail', methods=['GET'])
def get_layer_thumbnail(username, layername):
    app.logger.info('GET Layer Thumbnail')

    # USER
    if not re.match(username_re, username):
        raise LaymanError(2, {'parameter': 'user', 'expected': username_re})
    if username in PG_NON_USER_SCHEMAS:
        raise LaymanError(8, {'schema': username})
    if username in GS_RESERVED_WORKSPACE_NAMES:
        raise LaymanError(13, {'workspace': username})

    # LAYER
    if not re.match(layername_re, layername):
        raise LaymanError(2, {'parameter': 'layername', 'expected':
            layername_re})


    thumbnail_path = thumbnail.get_layer_thumbnail_path(username,
                                                            layername)
    if thumbnail_path is not None:
        userdir = filesystem.get_user_dir(username)
        thumbnail_path = os.path.join(userdir, thumbnail_path)
        return send_file(thumbnail_path, mimetype='image/png')

    raise LaymanError(16, {'layername': layername})



@app.errorhandler(LaymanError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response