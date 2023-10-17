import shutil
import tempfile
import logging
from flask import Blueprint, jsonify, request, current_app as app, g

from layman.common import rest as rest_util
from layman.common.prime_db_schema import publications
from layman.http import LaymanError
from layman.util import check_workspace_name_decorator
from layman import settings, authn, util as layman_util
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, LAYER_REST_PATH_NAME, LAYER_TYPE
from .filesystem import input_file, input_style, input_chunk, util as fs_util

bp = Blueprint('rest_workspace_layer', __name__)
logger = logging.getLogger(__name__)


@bp.before_request
@check_workspace_name_decorator
@util.check_layername_decorator
@authenticate
@authorize_workspace_publications_decorator
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

    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    info = util.get_complete_layer_info(workspace, layername, x_forwarded_items=x_forwarded_items)

    return jsonify(info), 200


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>", methods=['PATCH'])
@util.lock_decorator
def patch(workspace, layername):
    app.logger.info(f"PATCH Layer, actor={g.user}")

    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)

    info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername,
                                            context={'keys': ['title', 'name', 'description', 'table_uri', 'geodata_type', 'style_type',
                                                              'original_data_source', ]})
    kwargs = {
        'title': info.get('title', info['name']) or '',
        'description': info.get('description', '') or '',
    }

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

    external_table_uri_str = request.form.get('external_table_uri', '')
    if input_files and external_table_uri_str:
        raise LaymanError(48, {
            'parameters': ['file', 'external_table_uri'],
            'message': 'Both `file` and `external_table_uri` parameters are filled',
            'expected': 'Only one of the parameters is fulfilled.',
            'found': {
                'file': input_files.raw_paths,
                'external_table_uri': external_table_uri_str,
            }})

    # CRS
    crs_id = None
    if len(request.form.get('crs', '')) > 0:
        crs_id = request.form['crs']
        if crs_id not in settings.INPUT_SRS_LIST:
            raise LaymanError(2, {'parameter': 'crs', 'supported_values': settings.INPUT_SRS_LIST})
    check_crs = crs_id is None

    if crs_id and not input_files:
        raise LaymanError(48, {
            'parameters': ['crs', 'file'],
            'message': 'Parameter `crs` needs also parameter `file`.',
            'expected': 'Input files in `file` parameter or empty `crs` parameter.',
            'found': {
                'crs': crs_id,
                'file': request.form.getlist('file'),
            }})

    external_table_uri = util.parse_and_validate_external_table_uri_str(external_table_uri_str) if external_table_uri_str else None if input_files or info.get('original_data_source') == settings.EnumOriginalDataSource.FILE.value else info.get('_table_uri')

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
    if len(input_files.raw_paths) > 0 or external_table_uri:
        delete_from = 'layman.layer.filesystem.input_file'

    # Overview resampling
    overview_resampling = request.form.get('overview_resampling', '')
    if overview_resampling and overview_resampling not in settings.OVERVIEW_RESAMPLING_METHOD_LIST:
        raise LaymanError(2, {'expected': 'Resampling method for gdaladdo utility, https://gdal.org/programs/gdaladdo.html',
                              'parameter': 'overview_resampling',
                              'detail': {'found': 'no_overview_resampling',
                                         'supported_values': settings.OVERVIEW_RESAMPLING_METHOD_LIST}, })
    if len(input_files.raw_paths) == 0 and overview_resampling:
        raise LaymanError(48, f'Parameter overview_resampling requires parameter file to be set.')
    kwargs['overview_resampling'] = overview_resampling

    # Timeseries regex
    time_regex = request.form.get('time_regex') or None
    slugified_time_regex = input_file.slugify_timeseries_filename_pattern(time_regex) if time_regex else None
    if time_regex:
        if len(input_files.raw_paths) == 0:
            raise LaymanError(48, f'Parameter time_regex is allowed only in combination with files.')
        try:
            import re
            re.compile(time_regex)
        except re.error as exp:
            raise LaymanError(2, {'parameter': 'time_regex',
                                  'expected': 'Regular expression',
                                  }) from exp
    time_regex_format = request.form.get('time_regex_format') or None
    if time_regex_format and not time_regex:
        raise LaymanError(48, {
            'parameters': ['time_regex_format'],
            'message': 'Parameter `time_regex_format` needs also parameter `time_regex`.',
            'expected': 'Image mosaic regex in `time_regex` parameter or empty `time_regex_format` parameter.',
            'found': {
                'time_regex_format': time_regex_format,
            }})
    slugified_time_regex_format = input_file.slugify_timeseries_filename_pattern(time_regex_format) if time_regex_format else None

    name_normalized_tif_by_layer = time_regex is None
    name_input_file_by_layer = time_regex is None or input_files.is_one_archive
    enable_more_main_files = time_regex is not None

    # FILE NAMES
    use_chunk_upload = bool(input_files.sent_paths)
    if delete_from == 'layman.layer.filesystem.input_file' and input_files:
        if not (use_chunk_upload and input_files.is_one_archive):
            input_file.check_filenames(workspace, layername, input_files,
                                       check_crs, ignore_existing_files=True, enable_more_main_files=enable_more_main_files,
                                       time_regex=time_regex, slugified_time_regex=slugified_time_regex,
                                       name_input_file_by_layer=name_input_file_by_layer)
        # file checks
        if not use_chunk_upload:
            temp_dir = tempfile.mkdtemp(prefix="layman_")
            input_file.save_layer_files(workspace, layername, input_files, check_crs, overview_resampling, output_dir=temp_dir, name_input_file_by_layer=name_input_file_by_layer)

    if input_files.raw_paths:
        geodata_type = input_file.get_file_type(input_files.raw_or_archived_main_file_path)
    elif external_table_uri:
        geodata_type = settings.GEODATA_TYPE_VECTOR
    else:
        geodata_type = info['geodata_type']
    if style_type:
        style_type_for_check = style_type.code
    else:
        style_type_for_check = info['_style_type']
    if geodata_type == settings.GEODATA_TYPE_RASTER and style_type_for_check == 'qml':
        raise LaymanError(48, f'Raster layers are not allowed to have QML style.')
    kwargs['geodata_type'] = geodata_type

    kwargs['time_regex'] = time_regex
    kwargs['slugified_time_regex'] = slugified_time_regex
    kwargs['slugified_time_regex_format'] = slugified_time_regex_format
    kwargs['image_mosaic'] = time_regex is not None if delete_from == 'layman.layer.filesystem.input_file' else None
    kwargs['name_normalized_tif_by_layer'] = name_normalized_tif_by_layer
    kwargs['name_input_file_by_layer'] = name_input_file_by_layer
    kwargs['enable_more_main_files'] = enable_more_main_files

    props_to_refresh = util.get_same_or_missing_prop_names(workspace, layername)
    kwargs['metadata_properties_to_refresh'] = props_to_refresh
    kwargs['external_table_uri'] = external_table_uri
    is_external_table = not input_files and (bool(external_table_uri) or info.get('original_data_source') == settings.EnumOriginalDataSource.TABLE.value)
    kwargs['original_data_source'] = settings.EnumOriginalDataSource.TABLE.value if is_external_table else settings.EnumOriginalDataSource.FILE.value

    layer_result = {}

    kwargs.update({'actor_name': authn.get_authn_username()})
    rest_util.setup_patch_access_rights(request.form, kwargs)
    util.pre_publication_action_check(workspace,
                                      layername,
                                      kwargs,
                                      )

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
            input_style.save_layer_file(workspace, layername, style_file, style_type, )

        kwargs.update({
            'crs_id': crs_id,
            'http_method': request_method,
            'metadata_properties_to_refresh': props_to_refresh,
        })

        if delete_from == 'layman.layer.filesystem.input_file':

            if use_chunk_upload:
                files_to_upload = input_chunk.save_layer_files_str(
                    workspace, layername, input_files, check_crs, name_input_file_by_layer=name_input_file_by_layer)
                layer_result.update({
                    'files_to_upload': files_to_upload,
                })
                kwargs.update({
                    'check_crs': check_crs,
                })
            elif input_files:
                shutil.move(temp_dir, input_file.get_layer_input_file_dir(workspace, layername))
        publications.set_wfs_wms_status(workspace, LAYER_TYPE, layername, settings.EnumWfsWmsStatus.PREPARING)

    util.patch_layer(
        workspace,
        layername,
        kwargs,
        delete_from,
        'layman.layer.filesystem.input_chunk' if use_chunk_upload else delete_from
    )

    app.logger.info('PATCH Layer changes done')
    info = util.get_complete_layer_info(workspace, layername, x_forwarded_items=x_forwarded_items)
    info.update(layer_result)

    return jsonify(info), 200


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>", methods=['DELETE'])
@util.lock_decorator
def delete_layer(workspace, layername):
    app.logger.info(f"DELETE Layer, actor={g.user}")
    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)

    info = util.get_complete_layer_info(workspace, layername, x_forwarded_items=x_forwarded_items)

    util.abort_layer_chain(workspace, layername)

    util.delete_layer(workspace, layername)

    app.logger.info('DELETE Layer done')

    return jsonify({
        'name': layername,
        'url': info['url'],
        'uuid': info['uuid'],
    }), 200
