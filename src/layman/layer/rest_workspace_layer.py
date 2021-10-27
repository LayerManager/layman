import shutil
import tempfile
from flask import Blueprint, jsonify, request, current_app as app, g

from layman.common import rest as rest_util
from layman.http import LaymanError
from layman.util import check_workspace_name_decorator
from layman import settings, authn, util as layman_util
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, LAYER_REST_PATH_NAME, LAYER_TYPE
from .filesystem import input_file, input_style, input_chunk, util as fs_util

bp = Blueprint('rest_workspace_layer', __name__)


@bp.before_request
@check_workspace_name_decorator
@util.check_layername_decorator
@authenticate
@authorize_workspace_publications_decorator
@util.info_decorator
def before_request():
    pass


@bp.after_request
def after_request(response):
    layman_util.check_deprecated_url(response)
    return response


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>", methods=['GET'])
def get(workspace, layername):
    # pylint: disable=unused-argument
    app.logger.info(f"GET Layer, actor={g.user}")

    info = util.get_complete_layer_info(cached=True)

    return jsonify(info), 200


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>", methods=['PATCH'])
@util.lock_decorator
def patch(workspace, layername):
    app.logger.info(f"PATCH Layer, actor={g.user}")

    info = util.get_complete_layer_info(cached=True)
    kwargs = {
        'title': info.get('title', info['name']) or '',
        'description': info.get('description', '') or '',
    }

    # FILE
    use_chunk_upload = False
    zipped_file = None
    files = []
    if 'file' in request.files:
        files = [
            f for f in request.files.getlist("file")
            if len(f.filename) > 0
        ]
        if len(files) == 1 and input_file.get_compressed_main_file_extension(files[0].filename):
            zipped_file = files[0]
    if len(files) == 0 and len(request.form.getlist('file')) > 0:
        files = [
            filename for filename in request.form.getlist('file')
            if len(filename) > 0
        ]
        if len(files) > 0:
            use_chunk_upload = True
        if len(files) == 1 and input_file.get_compressed_main_file_extension(files[0]):
            zipped_file = files[0]

    # CRS
    crs_id = None
    if len(files) > 0 and len(request.form.get('crs', '')) > 0:
        crs_id = request.form['crs']
        if crs_id not in settings.INPUT_SRS_LIST:
            raise LaymanError(2, {'parameter': 'crs', 'supported_values': settings.INPUT_SRS_LIST})
    check_crs = crs_id is None

    # TITLE
    if len(request.form.get('title', '')) > 0:
        kwargs['title'] = request.form['title']

    # DESCRIPTION
    if len(request.form.get('description', '')) > 0:
        kwargs['description'] = request.form['description']

    # SLD
    style_file = None
    if 'style' in request.files and not request.files['style'].filename == '':
        style_file = request.files['style']
    elif 'sld' in request.files and not request.files['sld'].filename == '':
        style_file = request.files['sld']

    delete_from = None
    style_type = None
    if style_file:
        style_type = input_style.get_style_type_from_file_storage(style_file)
        kwargs['style_type'] = style_type
        kwargs['store_in_geoserver'] = style_type.store_in_geoserver
        delete_from = 'layman.layer.qgis.wms'
    if len(files) > 0:
        delete_from = 'layman.layer.filesystem.input_file'

    # FILE NAMES
    filenames = None
    if delete_from == 'layman.layer.filesystem.input_file':
        if use_chunk_upload and zipped_file:
            filenames = list()
        elif use_chunk_upload:
            filenames = files
        elif zipped_file:
            filenames = fs_util.get_filenames_from_zip_storage(zipped_file, with_zip_in_path=True)
        else:
            filenames = [f.filename for f in files]
        if not (use_chunk_upload and zipped_file):
            input_file.check_filenames(workspace, layername, filenames,
                                       check_crs, ignore_existing_files=True)
        # file checks
        if not use_chunk_upload:
            temp_dir = tempfile.mkdtemp(prefix="layman_")
            if zipped_file:
                input_file.save_layer_zip_file(workspace, layername, zipped_file, output_dir=temp_dir)
            else:
                input_file.save_layer_files(workspace, layername, files, check_crs, output_dir=temp_dir)

    if filenames:
        file_type = input_file.get_file_type(input_file.get_main_file_name(filenames))
    else:
        file_type = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['file']})['file']['file_type']
    if style_type:
        style_type_for_check = style_type.code
    else:
        style_type_for_check = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['style']})['style']['type']
    if file_type == settings.FILE_TYPE_RASTER and style_type_for_check == 'qml':
        raise LaymanError(48, f'Raster layers are not allowed to have QML style.')

    props_to_refresh = util.get_same_or_missing_prop_names(workspace, layername)
    kwargs['metadata_properties_to_refresh'] = props_to_refresh

    layer_result = {}

    if delete_from is not None:
        request_method = request.method.lower()
        deleted = util.delete_layer(workspace, layername, source=delete_from, http_method=request_method)
        if style_file is None:
            try:
                style_file = deleted['style']['file']
            except KeyError:
                pass
        style_type = input_style.get_style_type_from_file_storage(style_file)
        kwargs['style_type'] = style_type
        kwargs['store_in_geoserver'] = style_type.store_in_geoserver
        if style_file:
            input_style.save_layer_file(workspace, layername, style_file, style_type)

        kwargs.update({
            'crs_id': crs_id,
            'ensure_user': False,
            'http_method': request_method,
            'metadata_properties_to_refresh': props_to_refresh,
        })

        if delete_from == 'layman.layer.filesystem.input_file':

            if use_chunk_upload:
                files_to_upload = input_chunk.save_layer_files_str(
                    workspace, layername, files, check_crs)
                layer_result.update({
                    'files_to_upload': files_to_upload,
                })
                kwargs.update({
                    'check_crs': check_crs,
                })
            else:
                shutil.move(temp_dir, input_file.get_layer_input_file_dir(workspace, layername))
    kwargs.update({'actor_name': authn.get_authn_username()})

    rest_util.setup_patch_access_rights(request.form, kwargs)
    util.pre_publication_action_check(workspace,
                                      layername,
                                      kwargs,
                                      )

    util.patch_layer(
        workspace,
        layername,
        kwargs,
        delete_from,
        'layman.layer.filesystem.input_chunk' if use_chunk_upload else delete_from
    )

    app.logger.info('PATCH Layer changes done')
    info = util.get_complete_layer_info(workspace, layername)
    info.update(layer_result)

    return jsonify(info), 200


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>", methods=['DELETE'])
@util.lock_decorator
def delete_layer(workspace, layername):
    app.logger.info(f"DELETE Layer, actor={g.user}")

    info = util.get_complete_layer_info(cached=True)

    util.abort_layer_chain(workspace, layername)

    util.delete_layer(workspace, layername)

    app.logger.info('DELETE Layer done')

    return jsonify({
        'name': layername,
        'url': info['url'],
        'uuid': info['uuid'],
    }), 200
