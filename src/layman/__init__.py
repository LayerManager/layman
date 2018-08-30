import base64
import re

from flask import Flask, request, redirect, jsonify, url_for, send_file

from layman import db
from layman import filesystem
from layman.filesystem import thumbnail, get_user_dir
from layman.filesystem import input_files
from layman import geoserver
from layman.geoserver import sld
from layman import util
from .http import LaymanError
from .settings import *

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

@app.route('/')
def index():
    return redirect('/static/test-client/index.html')


@app.route('/rest/<username>/layers', methods=['GET'])
def get_layers(username):
    app.logger.info('GET Layers')

    # USER
    util.check_username(username)

    layernames = util.get_layer_names(username)

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
    util.check_username(username)

    # FILE
    if 'file' not in request.files:
        raise LaymanError(1, {'parameter': 'file'})
    files = request.files.getlist("file")

    # NAME
    unsafe_layername = request.form.get('name', '')
    if len(unsafe_layername) == 0:
        unsafe_layername = input_files.get_unsafe_layername(files)
    layername = util.to_safe_layer_name(unsafe_layername)
    util.check_layername(layername)
    info = util.get_layer_info(username, layername)
    if info:
        raise LaymanError(17, {layername: layername})
    util.check_new_layername(username, layername)

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
    geoserver.publish_layer_from_db(username, layername, description, title)

    # create SLD style
    geoserver.sld.create_layer_style(username, layername, sld_file)

    # generate thumbnail
    filesystem.thumbnail.generate_layer_thumbnail(username, layername)

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
    util.check_username(username)

    # LAYER
    util.check_layername(layername)


    info = util.get_complete_layer_info(username, layername)

    return jsonify(info), 200


@app.route('/rest/<username>/layers/<layername>', methods=['PUT'])
def put_layer(username, layername):
    app.logger.info('PUT Layer')

    # USER
    util.check_username(username)

    info = util.get_complete_layer_info(username, layername)

    # FILE
    files = request.files.getlist("file")

    # CRS
    crs_id = None
    if 'file' in request.files and len(request.form.get('crs', '')) > 0:
        crs_id = request.form['crs']
        if crs_id not in INPUT_SRS_LIST:
            raise LaymanError(2, {'parameter': 'crs', 'supported_values':
                INPUT_SRS_LIST})
    check_crs = crs_id is None

    update_info = False

    # TITLE
    if len(request.form.get('title', '')) > 0:
        info['title'] = request.form['title']
        update_info = True

    # DESCRIPTION
    if len(request.form.get('description', '')) > 0:
        info['description'] = request.form['description']
        update_info = True

    # SLD
    sld_file = None
    if 'sld' in request.files:
        sld_file = request.files['sld']

    delete_from = None
    if sld_file is not None:
        delete_from = 'layman.geoserver.sld'
    if len(files) > 0:
        delete_from = 'layman.filesystem.input_files'

    if update_info and delete_from != 'layman.filesystem.input_files':
        util.update_layer(username, layername, info)
    if delete_from is not None:
        deleted = util.delete_layer(username, layername, source=delete_from)
        if delete_from == 'layman.filesystem.input_files':

            # save files
            main_filename = input_files.save_layer_files(username, layername,
                                                         files)
            userdir = get_user_dir(username)
            main_filepath = os.path.join(userdir, main_filename)
            if check_crs:
                input_files.check_layer_crs(main_filepath)

            # import into DB table
            db.import_layer_vector_file(username, layername, main_filepath,
                                        crs_id)

            # publish layer to GeoServer
            geoserver.ensure_user_workspace(username)
            geoserver.publish_layer_from_db(username, layername,
                                            info['description'], info['title'])

        if sld_file is None:
            sld_file = deleted['sld']['file']

        # create SLD style
        geoserver.sld.create_layer_style(username, layername, sld_file)

        # generate thumbnail
        filesystem.thumbnail.generate_layer_thumbnail(username, layername)

    app.logger.info('PUT Layer changes done')
    info = util.get_complete_layer_info(username, layername)

    return jsonify(info), 200


@app.route('/rest/<username>/layers/<layername>/thumbnail', methods=['GET'])
def get_layer_thumbnail(username, layername):
    app.logger.info('GET Layer Thumbnail')

    # USER
    util.check_username(username)

    # LAYER
    util.check_layername(layername)


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