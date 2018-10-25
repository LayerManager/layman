import time

from flask import Flask, request, redirect, jsonify, url_for, send_file

from layman import db
from layman import filesystem
from layman.filesystem import thumbnail, get_user_dir
from layman.filesystem import input_files
from layman.filesystem import input_sld
from layman import geoserver
from .make_celery import make_celery
from .http import LaymanError
from .settings import *

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

celery_app = make_celery(app)
from layman import util
from layman.db import tasks
from layman.geoserver import tasks
from layman.filesystem import tasks


celery_tasks = {}

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

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        msg = '{:s} function took {:.3f} ms'.format(f.__name__, (time2-time1)*1000.0)
        # app.logger.info(msg)
        # print(msg)

        return ret
    return wrap



@app.route('/rest/<username>/layers', methods=['POST'])
def post_layers(username):
    app.logger.info('POST Layers')

    # USER
    util.check_username(username)

    # FILE
    use_chunk_upload = False
    if 'file' in request.files:
        files = request.files.getlist("file")
    elif len(request.form.getlist('file')) > 0:
        files = request.form.getlist('file')
        use_chunk_upload = True
    else:
        raise LaymanError(1, {'parameter': 'file'})


    # NAME
    unsafe_layername = request.form.get('name', '')
    if len(unsafe_layername) == 0:
        unsafe_layername = input_files.get_unsafe_layername(files)
    layername = util.to_safe_layer_name(unsafe_layername)
    util.check_layername(layername)
    info = util.get_layer_info(username, layername)
    if info:
        raise LaymanError(17, {'layername': layername})
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

    task_options = {
        'crs_id': crs_id,
        'description': description,
        'title': title,
        'ensure_user': True,
        'check_crs': False,
    }

    layerurl = url_for('get_layer', layername=layername, username=username)

    layer_result = {
        'name': layername,
        'url': layerurl,
    }

    # save files
    filesystem.ensure_user_dir(username)
    input_sld.save_layer_file(username, layername, sld_file)
    if use_chunk_upload:
        files_to_upload = input_files.save_layer_files_str(
            username, layername, files, check_crs, request.endpoint)
        layer_result.update({
            'files_to_upload': files_to_upload,
        })
        task_options.update({
            'check_crs': check_crs,
        })
    else:
        input_files.save_layer_files(
            username, layername, files, check_crs)

    util.post_layer(username, layername, task_options, use_chunk_upload)

    # app.logger.info('uploaded layer '+layername)
    return jsonify([layer_result]), 200

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

    # LAYER
    util.check_layername(layername)

    if not util.is_layer_last_task_ready(username, layername):
        raise LaymanError(19)

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
        if sld_file is None:
            sld_file = deleted['sld']['file']
        input_sld.save_layer_file(username, layername, sld_file)

        if delete_from == 'layman.filesystem.input_files':

            # save files
            input_files.save_layer_files(username, layername,
                                                         files, check_crs)

        task_options = {
            'crs_id': crs_id,
            'description': info['description'],
            'title': info['title'],
            'ensure_user': False,
        }
        util.put_layer(username, layername, delete_from, task_options)

    app.logger.info('PUT Layer changes done')
    info = util.get_complete_layer_info(username, layername)

    return jsonify(info), 200


@app.route('/rest/<username>/layers/<layername>', methods=['DELETE'])
def delete_layer(username, layername):
    app.logger.info('DELETE Layer')

    # USER
    util.check_username(username)

    # LAYER
    util.check_layername(layername)

    # raise exception if layer does not exist
    info = util.get_complete_layer_info(username, layername)

    util.abort_layer_tasks(username, layername)

    util.delete_layer(username, layername)

    app.logger.info('DELETE Layer done')

    return jsonify({
        'name': layername,
        'url': info['url'],
    }), 200


@app.route('/rest/<username>/layers/<layername>/thumbnail', methods=['GET'])
def get_layer_thumbnail(username, layername):
    app.logger.info('GET Layer Thumbnail')

    # USER
    util.check_username(username)

    # LAYER
    util.check_layername(layername)

    # raise exception if layer does not exist
    util.get_complete_layer_info(username, layername)

    thumbnail_path = thumbnail.get_layer_thumbnail_path(username,
                                                            layername)
    if thumbnail_path is not None:
        userdir = filesystem.get_user_dir(username)
        thumbnail_path = os.path.join(userdir, thumbnail_path)
        return send_file(thumbnail_path, mimetype='image/png')

    raise LaymanError(16, {'layername': layername})


@app.route("/rest/<username>/layers/<layername>/chunk", methods=['POST'])
def post_layer_chunk(username, layername):
    app.logger.info('POST Layer Chunk')

    # USER
    util.check_username(username)

    # LAYER
    util.check_layername(layername)

    total_chunks = request.form.get('resumableTotalChunks', type=int)
    chunk_number = request.form.get('resumableChunkNumber', default=1,
                                            type=int)
    filename = request.form.get('resumableFilename', default='error',
                                         type=str)
    parameter_name = request.form.get('layman_original_parameter', default='error',
                                         type=str)
    chunk = request.files['file']

    input_files.save_layer_file_chunk(username, layername, parameter_name,
                                      filename, chunk,
                                      chunk_number, total_chunks)
    # time.sleep(5)

    return jsonify({
        'message': 'Chunk saved.'
    }), 200


@app.route("/rest/<username>/layers/<layername>/chunk", methods=['GET'])
def get_layer_chunk(username, layername):
    app.logger.info('GET Layer Chunk')

    chunk_number = request.args.get('resumableChunkNumber', default=1,
                                            type=int)
    filename = request.args.get('resumableFilename', default='error',
                                         type=str)
    parameter_name = request.args.get('layman_original_parameter', default='error',
                                         type=str)

    chunk_exists = input_files.layer_file_chunk_exists(
        username, layername, parameter_name, filename, chunk_number)

    if chunk_exists:
        return jsonify({
            'message': 'Chunk exists.'
        }), 200
    else:
        return jsonify({
            'message': 'Chunk not found.'
        }), 404


@app.errorhandler(LaymanError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response