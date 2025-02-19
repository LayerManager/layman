import json
import io

from flask import Blueprint, jsonify, request, current_app as app, g
from werkzeug.datastructures import FileStorage

from layman import authn, util as layman_util
from layman.common import rest as rest_util
from layman.util import check_workspace_name_decorator
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, MAP_REST_PATH_NAME, get_map_patch_keys
from .filesystem import input_file, thumbnail

bp = Blueprint('rest_workspace_map', __name__)


@bp.before_request
@check_workspace_name_decorator
@util.check_mapname_decorator
@authenticate
@authorize_workspace_publications_decorator
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>", methods=['GET'])
def get(workspace, mapname):
    # pylint: disable=unused-argument
    app.logger.info(f"GET Map, actor={g.user}")

    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    info = util.get_complete_map_info(workspace, mapname, x_forwarded_items=x_forwarded_items)

    return jsonify(info), 200


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>", methods=['PATCH'])
@util.lock_decorator
def patch(workspace, mapname):
    app.logger.info(f"PATCH Map, actor={g.user}")

    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    info = util.get_complete_map_info(workspace, mapname)

    # FILE
    file = None
    file_json = {}
    if 'file' in request.files and not request.files['file'].filename == '':
        file = request.files["file"]
    if file is not None:
        file_json = util.check_file(file)

    # TITLE
    if len(request.form.get('title', '')) > 0:
        title = request.form['title']
    elif len(file_json.get('title', '')) > 0:
        title = file_json['title']
    else:
        title = info['title']

    # DESCRIPTION
    if len(request.form.get('description', '')) > 0:
        description = request.form['description']
    elif len(file_json.get('abstract', '')) > 0:
        description = file_json['abstract']
    else:
        description = info['description']

    props_to_refresh = util.get_same_or_missing_prop_names(workspace, mapname)
    metadata_properties_to_refresh = props_to_refresh
    file_changed = file is not None
    kwargs = {
        'title': title,
        'description': description,
        'file_changed': file_changed,
        'http_method': 'patch',
        'metadata_properties_to_refresh': metadata_properties_to_refresh,
        'actor_name': authn.get_authn_username(),
        'x_forwarded_headers': x_forwarded_items.headers,
        'uuid': info['uuid'],
    }

    rest_util.setup_patch_access_rights(request.form, kwargs)
    util.pre_publication_action_check(workspace,
                                      mapname,
                                      kwargs,
                                      )

    if file is not None:
        thumbnail.delete_map_by_uuid(info['uuid'])
        file = FileStorage(
            io.BytesIO(json.dumps(file_json).encode()),
            file.filename
        )
        input_file.save_map_files(info['uuid'], [file])

    util.patch_map(
        workspace,
        mapname,
        kwargs,
        'layman.map.filesystem.input_file' if file_changed else None
    )

    patch_keys = get_map_patch_keys()
    info = util.get_map_info(workspace, mapname, context={'keys': patch_keys, 'x_forwarded_items': x_forwarded_items})
    info['url'] = layman_util.get_workspace_publication_url(info['type'], workspace, mapname, x_forwarded_items=x_forwarded_items)
    info = {key: value for key, value in info.items() if key in patch_keys}

    return jsonify(info), 200


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>", methods=['DELETE'])
@util.lock_decorator
def delete_map(workspace, mapname):
    app.logger.info(f"DELETE Map, actor={g.user}")
    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)

    # raise exception if map does not exist
    info = util.get_complete_map_info(workspace, mapname, x_forwarded_items=x_forwarded_items)

    util.abort_map_chain(workspace, mapname)

    util.delete_map(workspace, mapname)

    app.logger.info('DELETE Map done')

    return jsonify({
        'name': mapname,
        'url': info['url'],
        'uuid': info['uuid'],
    }), 200
