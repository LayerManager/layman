from flask import Blueprint, jsonify, request, g
from flask import current_app as app

from layman.http import LaymanError
from layman.util import check_workspace_name_decorator, url_for
from layman import settings, authn, util as layman_util
from layman.authn import authenticate, get_authn_username
from layman.authz import authorize_workspace_publications_decorator
from layman.common import redis as redis_util, rest as rest_common
from . import util, LAYER_TYPE, LAYER_REST_PATH_NAME
from .filesystem import input_file, input_style, input_chunk, uuid, util as fs_util

bp = Blueprint('rest_workspace_layers', __name__)


@bp.before_request
@check_workspace_name_decorator
@authenticate
@authorize_workspace_publications_decorator
def before_request():
    pass


@bp.after_request
def after_request(response):
    layman_util.check_deprecated_url(response)
    return response


@bp.route(f"/{LAYER_REST_PATH_NAME}", methods=['GET'])
def get(workspace):
    app.logger.info(f"GET Layers, actor={g.user}")

    actor = get_authn_username()
    return rest_common.get_publications(LAYER_TYPE, actor, request_args=request.args, workspace=workspace)


@bp.route(f"/{LAYER_REST_PATH_NAME}", methods=['POST'])
def post(workspace):
    app.logger.info(f"POST Layers, actor={g.user}")

    # FILE
    sent_file_streams = []
    sent_file_paths = []
    if 'file' in request.files:
        sent_file_streams = [
            f for f in request.files.getlist("file")
            if len(f.filename) > 0
        ]
    if len(sent_file_streams) == 0 and len(request.form.getlist('file')) > 0:
        sent_file_paths = [
            filename for filename in request.form.getlist('file')
            if len(filename) > 0
        ]
    input_files = fs_util.InputFiles(sent_streams=sent_file_streams, sent_paths=sent_file_paths)

    # DB_CONNECTION
    db_connection_string = request.form.get('db_connection', '')
    if not input_files and not db_connection_string:
        raise LaymanError(1, {
            'parameters': ['file', 'db_connection'],
            'message': 'Both `file` and `db_connection` parameters are empty',
            'expected': 'One of the parameters is filled.',
        })
    if input_files and db_connection_string:
        raise LaymanError(48, {
            'parameters': ['file', 'db_connection'],
            'message': 'Both `file` and `db_connection` parameters are filled',
            'expected': 'Only one of the parameters is fulfilled.',
            'found': {
                'file': input_files.raw_paths,
                'db_connection': db_connection_string,
            }})

    db_connection = util.parse_and_validate_connection_string(db_connection_string) if db_connection_string else None

    # NAME
    unsafe_layername = request.form.get('name', '')
    if len(unsafe_layername) == 0:
        unsafe_layername = input_file.get_unsafe_layername(input_files)
    layername = util.to_safe_layer_name(unsafe_layername)
    util.check_layername(layername)
    info = util.get_layer_info(workspace, layername)
    if info:
        raise LaymanError(17, {'layername': layername})

    # CRS
    crs_id = None
    if len(request.form.get('crs', '')) > 0:
        crs_id = request.form['crs']
        if crs_id not in settings.INPUT_SRS_LIST:
            raise LaymanError(2, {'parameter': 'crs', 'supported_values': settings.INPUT_SRS_LIST})
    check_crs = crs_id is None

    # Timeseries regex
    time_regex = request.form.get('time_regex') or None
    slugified_time_regex = input_file.slugify_timeseries_filename_pattern(time_regex) if time_regex else None
    if time_regex:
        try:
            import re
            re.compile(time_regex)
        except re.error as exp:
            raise LaymanError(2, {'parameter': 'time_regex',
                                  'expected': 'Regular expression',
                                  }) from exp

    name_normalized_tif_by_layer = time_regex is None
    name_input_file_by_layer = time_regex is None or input_files.is_one_archive
    enable_more_main_files = time_regex is not None

    # FILE NAMES
    use_chunk_upload = bool(input_files.sent_paths)
    if not (use_chunk_upload and input_files.is_one_archive) and input_files:
        input_file.check_filenames(workspace, layername, input_files, check_crs,
                                   enable_more_main_files=enable_more_main_files, time_regex=time_regex,
                                   slugified_time_regex=slugified_time_regex,
                                   name_input_file_by_layer=name_input_file_by_layer)
    file_type = input_file.get_file_type(input_files.raw_or_archived_main_file_path) if not db_connection else settings.FILE_TYPE_VECTOR

    # TITLE
    if len(request.form.get('title', '')) > 0:
        title = request.form['title']
    else:
        title = layername

    # DESCRIPTION
    description = request.form.get('description', '')

    # Style
    style_file = None
    if 'style' in request.files and not request.files['style'].filename == '':
        style_file = request.files['style']
    elif 'sld' in request.files and not request.files['sld'].filename == '':
        style_file = request.files['sld']
    style_type = input_style.get_style_type_from_file_storage(style_file)

    if file_type == settings.FILE_TYPE_RASTER and style_type.code == 'qml':
        raise LaymanError(48, f'Raster layers are not allowed to have QML style.')

    # Overview resampling
    overview_resampling = request.form.get('overview_resampling', '')
    if overview_resampling and overview_resampling not in settings.OVERVIEW_RESAMPLING_METHOD_LIST:
        raise LaymanError(2, {'expected': 'Resampling method for gdaladdo utility, https://gdal.org/programs/gdaladdo.html',
                              'parameter': 'overview_resampling',
                              'detail': {'found': 'no_overview_resampling',
                                         'supported_values': settings.OVERVIEW_RESAMPLING_METHOD_LIST}, })

    actor_name = authn.get_authn_username()

    task_options = {
        'crs_id': crs_id,
        'description': description,
        'title': title,
        'check_crs': False,
        'actor_name': actor_name,
        'style_type': style_type,
        'store_in_geoserver': style_type.store_in_geoserver,
        'overview_resampling': overview_resampling,
        'file_type': file_type,
        'time_regex': time_regex,
        'slugified_time_regex': slugified_time_regex,
        'image_mosaic': time_regex is not None,
        'name_normalized_tif_by_layer': name_normalized_tif_by_layer,
        'name_input_file_by_layer': name_input_file_by_layer,
        'enable_more_main_files': enable_more_main_files,
    }

    rest_common.setup_post_access_rights(request.form, task_options, actor_name)
    util.pre_publication_action_check(workspace,
                                      layername,
                                      task_options,
                                      )

    layerurl = url_for('rest_workspace_layer.get', layername=layername, workspace=workspace)

    layer_result = {
        'name': layername,
        'url': layerurl,
    }

    redis_util.create_lock(workspace, LAYER_TYPE, layername, request.method)

    try:
        # register layer uuid
        uuid_str = uuid.assign_layer_uuid(workspace, layername)
        layer_result.update({
            'uuid': uuid_str,
        })
        task_options.update({'uuid': uuid_str, })

        # save files
        input_style.save_layer_file(workspace, layername, style_file, style_type)
        if use_chunk_upload:
            files_to_upload = input_chunk.save_layer_files_str(
                workspace, layername, input_files, check_crs, name_input_file_by_layer=name_input_file_by_layer)
            layer_result.update({
                'files_to_upload': files_to_upload,
            })
            task_options.update({
                'check_crs': check_crs,
            })
        elif input_files:
            try:
                input_file.save_layer_files(workspace, layername, input_files, check_crs, overview_resampling, name_input_file_by_layer=name_input_file_by_layer)
            except BaseException as exc:
                uuid.delete_layer(workspace, layername)
                input_file.delete_layer(workspace, layername)
                raise exc

        util.post_layer(
            workspace,
            layername,
            task_options,
            'layman.layer.filesystem.input_chunk' if use_chunk_upload else 'layman.layer.filesystem.input_file'
        )
    except Exception as exc:
        try:
            if util.is_layer_chain_ready(workspace, layername):
                redis_util.unlock_publication(workspace, LAYER_TYPE, layername)
        finally:
            redis_util.unlock_publication(workspace, LAYER_TYPE, layername)
        raise exc

    # app.logger.info('uploaded layer '+layername)
    return jsonify([layer_result]), 200


@bp.route(f"/{LAYER_REST_PATH_NAME}", methods=['DELETE'])
def delete(workspace):
    app.logger.info(f"DELETE Layers, actor={g.user}")

    infos = layman_util.delete_publications(workspace,
                                            LAYER_TYPE,
                                            util.is_layer_chain_ready,
                                            util.abort_layer_chain,
                                            util.delete_layer,
                                            request.method,
                                            'rest_workspace_layer.get',
                                            'layername',
                                            )
    return infos, 200
