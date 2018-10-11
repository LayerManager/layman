import time
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
from .make_celery import make_celery
from .http import LaymanError
from .settings import *

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

celery_app = make_celery(app)
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
    userdir = filesystem.ensure_user_dir(username)
    sld_file = None
    sld_path = None
    if 'sld' in request.files:
        sld_file = request.files['sld']
        sld_path = os.path.join(userdir, layername+'.sld')

    # save files
    main_filename = timing(input_files.save_layer_files)(username, layername,
                                                        files,
                                                 check_crs)
    main_filepath = os.path.join(userdir, main_filename)
    if sld_file is not None:
        sld_file.save(sld_path)

    # import into DB table
    db.ensure_user_schema(username)
    # timing(db.import_layer_vector_file)(username, layername, main_filepath, crs_id)
    res = db.tasks.import_layer_vector_file.apply_async(
        (username, layername, main_filepath, crs_id),
        queue=LAYMAN_CELERY_QUEUE)
    res.get()

    # publish layer to GeoServer
    geoserver.ensure_user_workspace(username)
    # timing(geoserver.publish_layer_from_db)(username, layername, description,
    #                                        title)
    res = geoserver.tasks.publish_layer_from_db.apply_async(
        (username, layername, description, title),
        queue=LAYMAN_CELERY_QUEUE)
    res.get()

    # create SLD style
    # timing(geoserver.sld.create_layer_style)(username, layername, sld_path)
    res = geoserver.tasks.create_layer_style.apply_async(
        (username, layername, sld_path),
        queue=LAYMAN_CELERY_QUEUE)
    res.get()

    # generate thumbnail
    # timing(filesystem.thumbnail.generate_layer_thumbnail)(username, layername)
    res = filesystem.tasks.generate_layer_thumbnail.apply_async(
        (username, layername),
        queue=LAYMAN_CELERY_QUEUE)
    res.get()

    layerurl = url_for('get_layer', layername=layername, username=username)

    app.logger.info('uploaded layer '+layername)
    return jsonify([{
        'name': layername,
        'url': layerurl,
    }]), 200

@app.route('/rest/<username>/test', methods=['GET'])
def test(username):
    app.logger.info('GET test')

    insp = celery_app.control.inspect()
    actives = str(insp.active())



    app.logger.info('GET test done')
    all_task_states = {id: r.state for id,r in celery_tasks.items()}
    tasks_to_kill = [r for r in celery_tasks.values() if r.state not in \
        ['SUCCESS', 'REVOKED']]

    for t in tasks_to_kill:
        app.logger.info('ABORTING '+t.id)
        t.abort()

    res = db.tasks.long.apply_async(('','','',''), queue=LAYMAN_CELERY_QUEUE)
    if isinstance(res.id, str) and len(res.id) > 0:
        celery_tasks[res.id] = res

    return jsonify([{
        'done': True,
        'tasks': all_task_states,
        'tasks_to_kill': [r.id for r in tasks_to_kill],
        'active_tasks': actives,
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

    # LAYER
    util.check_layername(layername)

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
    userdir = get_user_dir(username)
    sld_file = None
    sld_path = None
    if 'sld' in request.files:
        sld_file = request.files['sld']
        sld_path = os.path.join(userdir, layername+'.sld')

    delete_from = None
    if sld_file is not None:
        delete_from = 'layman.geoserver.sld'
    if len(files) > 0:
        delete_from = 'layman.filesystem.input_files'

    if update_info and delete_from != 'layman.filesystem.input_files':
        util.update_layer(username, layername, info)
    if delete_from is not None:
        deleted = util.delete_layer(username, layername, source=delete_from)
        if sld_file is not None:
            sld_file.save(sld_path)

        if delete_from == 'layman.filesystem.input_files':

            # save files
            main_filename = input_files.save_layer_files(username, layername,
                                                         files, check_crs)
            main_filepath = os.path.join(userdir, main_filename)

            # import into DB table
            db.import_layer_vector_file(username, layername, main_filepath,
                                        crs_id)

            # publish layer to GeoServer
            geoserver.ensure_user_workspace(username)
            geoserver.publish_layer_from_db(username, layername,
                                            info['description'], info['title'])

        if sld_file is None:
            sld_file = deleted['sld']['file']
            sld_path = os.path.join(userdir, layername + '.sld')
            with open(sld_path, 'wb') as out:
                out.write(sld_file.read())

        # create SLD style
        geoserver.sld.create_layer_style(username, layername, sld_path)

        # generate thumbnail
        filesystem.thumbnail.generate_layer_thumbnail(username, layername)

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



@app.errorhandler(LaymanError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response