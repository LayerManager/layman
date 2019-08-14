from flask import Blueprint, jsonify, request, url_for, g
from flask import current_app as app

from layman.http import LaymanError
from layman.util import check_username
from layman import settings
from . import util
from .filesystem import input_file, input_sld, input_chunk, uuid
from layman.authn import authenticate
from layman.authz import authorize


bp = Blueprint('rest_layers', __name__)

@bp.before_request
@authenticate
@authorize
def before_request():
    pass


@bp.route('/layers', methods=['GET'])
def get(username):
    app.logger.info(f"GET Layers, user={g.user and g.user['name']}")

    # USER
    check_username(username)

    layernames = util.get_layer_names(username)
    layernames.sort()

    infos = [
        {
            'name': layername,
            'url': url_for('rest_layer.get', layername=layername, username=username),
            'uuid': uuid.get_layer_uuid(username, layername),
        }
        for layername in layernames
    ]
    return jsonify(infos), 200


@bp.route('/layers', methods=['POST'])
def post(username):
    app.logger.info(f"POST Layers, user={g.user and g.user['name']}")

    # USER
    check_username(username)

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
        raise LaymanError(1, {'parameter': 'file'})

    # NAME
    unsafe_layername = request.form.get('name', '')
    if len(unsafe_layername) == 0:
        unsafe_layername = input_file.get_unsafe_layername(files)
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
        if crs_id not in settings.INPUT_SRS_LIST:
            raise LaymanError(2, {'parameter': 'crs', 'supported_values':
                settings.INPUT_SRS_LIST})
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
    if 'sld' in request.files and not request.files['sld'].filename == '':
        sld_file = request.files['sld']

    task_options = {
        'crs_id': crs_id,
        'description': description,
        'title': title,
        'ensure_user': True,
        'check_crs': False,
    }

    layerurl = url_for('rest_layer.get', layername=layername, username=username)

    layer_result = {
        'name': layername,
        'url': layerurl,
    }

    # FILE NAMES
    if use_chunk_upload:
        filenames = files
    else:
        filenames = [f.filename for f in files]
    input_file.check_filenames(username, layername, filenames, check_crs)

    # register layer uuid
    uuid_str = uuid.assign_layer_uuid(username, layername)
    layer_result.update({
        'uuid': uuid_str,
    })

    # save files
    input_sld.save_layer_file(username, layername, sld_file)
    if use_chunk_upload:
        files_to_upload = input_chunk.save_layer_files_str(
            username, layername, files, check_crs)
        layer_result.update({
            'files_to_upload': files_to_upload,
        })
        task_options.update({
            'check_crs': check_crs,
        })
    else:
        input_file.save_layer_files(
            username, layername, files, check_crs)

    util.post_layer(username, layername, task_options, use_chunk_upload)

    # app.logger.info('uploaded layer '+layername)
    return jsonify([layer_result]), 200

