from flask import Blueprint, jsonify, request, current_app as app, g

from layman.common import rest as rest_util
from layman.http import LaymanError
from layman.util import check_username_decorator
from layman import settings, authn
from . import util, LAYER_REST_PATH_NAME
from .filesystem import input_file, input_style, input_chunk
from layman.authn import authenticate
from layman.authz import authorize_publications_decorator

bp = Blueprint('rest_layer', __name__)


@bp.before_request
@check_username_decorator
@util.check_layername_decorator
@authenticate
@authorize_publications_decorator
@util.info_decorator
def before_request():
    pass


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>", methods=['GET'])
def get(username, layername):
    app.logger.info(f"GET Layer, user={g.user}")

    info = util.get_complete_layer_info(cached=True)

    return jsonify(info), 200


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>", methods=['PATCH'])
@util.lock_decorator
def patch(username, layername):
    app.logger.info(f"PATCH Layer, user={g.user}")

    info = util.get_complete_layer_info(cached=True)
    kwargs = {
        'title': info.get('title', info['name']),
        'description': info.get('description', ''),
    }

    # FILE
    use_chunk_upload = False
    files = []
    if 'file' in request.files:
        files = [
            f for f in request.files.getlist("file")
            if len(f.filename) > 0
        ]
    if len(files) == 0 and len(request.form.getlist('file')) > 0:
        files = [
            filename for filename in request.form.getlist('file')
            if len(filename) > 0
        ]
        if len(files) > 0:
            use_chunk_upload = True

    # CRS
    crs_id = None
    if len(files) > 0 and len(request.form.get('crs', '')) > 0:
        crs_id = request.form['crs']
        if crs_id not in settings.INPUT_SRS_LIST:
            raise LaymanError(2, {'parameter': 'crs', 'supported_values': settings.INPUT_SRS_LIST})
    check_crs = crs_id is None

    update_info = False

    # TITLE
    if len(request.form.get('title', '')) > 0:
        kwargs['title'] = request.form['title']
        update_info = True

    # DESCRIPTION
    if len(request.form.get('description', '')) > 0:
        kwargs['description'] = request.form['description']
        update_info = True

    # SLD
    style_file = None
    if 'style' in request.files and not request.files['style'].filename == '':
        style_file = request.files['style']
    elif 'sld' in request.files and not request.files['sld'].filename == '':
        style_file = request.files['sld']

    delete_from = None
    if style_file:
        style_type = input_style.get_style_type_from_file_storage(style_file)
        kwargs['style_type'] = style_type
        kwargs['store_in_geoserver'] = style_type.store_in_geoserver
        delete_from = 'layman.layer.qgis.wms'
    if len(files) > 0:
        delete_from = 'layman.layer.filesystem.input_file'

    # FILE NAMES
    if delete_from == 'layman.layer.filesystem.input_file':
        if use_chunk_upload:
            filenames = files
        else:
            filenames = [f.filename for f in files]
        input_file.check_filenames(username, layername, filenames,
                                   check_crs, ignore_existing_files=True)

    props_to_refresh = util.get_same_or_missing_prop_names(username, layername)
    kwargs['metadata_properties_to_refresh'] = props_to_refresh

    layer_result = {}

    if delete_from is not None:
        deleted = util.delete_layer(username, layername, source=delete_from, http_method='patch')
        if style_file is None:
            try:
                style_file = deleted['style']['file']
            except KeyError:
                pass
        style_type = input_style.get_style_type_from_file_storage(style_file)
        kwargs['style_type'] = style_type
        kwargs['store_in_geoserver'] = style_type.store_in_geoserver
        if style_file:
            input_style.save_layer_file(username, layername, style_file, style_type)

        kwargs.update({
            'crs_id': crs_id,
            'ensure_user': False,
            'http_method': 'patch',
            'metadata_properties_to_refresh': props_to_refresh,
        })

        if delete_from == 'layman.layer.filesystem.input_file':

            if use_chunk_upload:
                files_to_upload = input_chunk.save_layer_files_str(
                    username, layername, files, check_crs)
                layer_result.update({
                    'files_to_upload': files_to_upload,
                })
                kwargs.update({
                    'check_crs': check_crs,
                })
            else:
                input_file.save_layer_files(
                    username, layername, files, check_crs)
    kwargs.update({'actor_name': authn.get_authn_username()})

    rest_util.setup_patch_access_rights(request.form, kwargs)
    util.pre_publication_action_check(username,
                                      layername,
                                      kwargs,
                                      )

    util.patch_layer(
        username,
        layername,
        kwargs,
        delete_from,
        'layman.layer.filesystem.input_chunk' if use_chunk_upload else delete_from
    )

    app.logger.info('PATCH Layer changes done')
    info = util.get_complete_layer_info(username, layername)
    info.update(layer_result)

    return jsonify(info), 200


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>", methods=['DELETE'])
@util.lock_decorator
def delete_layer(username, layername):
    app.logger.info(f"DELETE Layer, user={g.user}")

    info = util.get_complete_layer_info(cached=True)

    util.abort_layer_tasks(username, layername)

    util.delete_layer(username, layername)

    app.logger.info('DELETE Layer done')

    return jsonify({
        'name': layername,
        'url': info['url'],
        'uuid': info['uuid'],
    }), 200
