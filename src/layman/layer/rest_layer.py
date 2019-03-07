from flask import Blueprint, jsonify, request
from flask import current_app as app

from layman.http import LaymanError
from layman.util import check_username
from layman.settings import *
from . import util
from .filesystem import input_files, input_sld


bp = Blueprint('rest_layer', __name__)


@bp.route('/layers/<layername>', methods=['GET'])
def get(username, layername):
    app.logger.info('GET Layer')

    # USER
    check_username(username)

    # LAYER
    util.check_layername(layername)


    info = util.get_complete_layer_info(username, layername)

    return jsonify(info), 200


@bp.route('/layers/<layername>', methods=['PUT'])
def put(username, layername):
    app.logger.info('PUT Layer')

    # USER
    check_username(username)

    # LAYER
    util.check_layername(layername)

    if not util.is_layer_last_task_ready(username, layername):
        raise LaymanError(19)

    info = util.get_complete_layer_info(username, layername)

    # FILE
    use_chunk_upload = False
    if 'file' in request.files:
        files = request.files.getlist("file")
    elif len(request.form.getlist('file')) > 0:
        files = list(filter(
            lambda f: len(f) > 0,
            request.form.getlist('file')
        ))
        if len(files):
            use_chunk_upload = True
    else:
        files = []

    # CRS
    crs_id = None
    if len(files) > 0 and len(request.form.get('crs', '')) > 0:
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
        delete_from = 'layman.layer.geoserver.sld'
    if len(files) > 0:
        delete_from = 'layman.layer.filesystem.input_files'

    if update_info and delete_from != 'layman.layer.filesystem.input_files':
        util.update_layer(username, layername, info)

    layer_result = {}

    if delete_from is not None:
        deleted = util.delete_layer(username, layername, source=delete_from)
        if sld_file is None:
            sld_file = deleted['sld']['file']
        input_sld.save_layer_file(username, layername, sld_file)

        task_options = {
            'crs_id': crs_id,
            'description': info['description'],
            'title': info['title'],
            'ensure_user': False,
        }

        if delete_from == 'layman.layer.filesystem.input_files':

            if use_chunk_upload:
                files_to_upload = input_files.save_layer_files_str(
                    username, layername, files, check_crs)
                layer_result.update({
                    'files_to_upload': files_to_upload,
                })
                task_options.update({
                    'check_crs': check_crs,
                })
            else:
                input_files.save_layer_files(
                    username, layername, files, check_crs)

        util.put_layer(username, layername, delete_from, task_options, use_chunk_upload)

    app.logger.info('PUT Layer changes done')
    info = util.get_complete_layer_info(username, layername)
    info.update(layer_result)

    return jsonify(info), 200


@bp.route('/layers/<layername>', methods=['DELETE'])
def delete_layer(username, layername):
    app.logger.info('DELETE Layer')

    # USER
    check_username(username)

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


