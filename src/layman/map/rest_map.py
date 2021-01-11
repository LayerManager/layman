import json
import io

from flask import Blueprint, jsonify, request, current_app as app, g
from werkzeug.datastructures import FileStorage

from layman.common import rest as rest_util
from layman.util import check_username_decorator
from . import util, MAP_REST_PATH_NAME
from .filesystem import input_file, thumbnail
from layman import authn
from layman.authn import authenticate
from layman.authz import authorize_publications_decorator

bp = Blueprint('rest_map', __name__)


@bp.before_request
@check_username_decorator
@util.check_mapname_decorator
@authenticate
@authorize_publications_decorator
@util.info_decorator
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>", methods=['GET'])
def get(username, mapname):
    app.logger.info(f"GET Map, user={g.user}")

    info = util.get_complete_map_info(cached=True)

    return jsonify(info), 200


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>", methods=['PATCH'])
@util.lock_decorator
def patch(username, mapname):
    app.logger.info(f"PATCH Map, user={g.user}")

    info = util.get_complete_map_info(cached=True)

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

    props_to_refresh = util.get_same_or_missing_prop_names(username, mapname)
    metadata_properties_to_refresh = props_to_refresh
    if file is not None:
        thumbnail.delete_map(username, mapname)
        file = FileStorage(
            io.BytesIO(json.dumps(file_json).encode()),
            file.filename
        )
        input_file.save_map_files(
            username, mapname, [file])

    file_changed = file is not None
    kwargs = {
        'title': title,
        'description': description,
        'file_changed': file_changed,
        'http_method': 'patch',
        'metadata_properties_to_refresh': metadata_properties_to_refresh,
        'actor_name': authn.get_authn_username(),
    }

    rest_util.setup_patch_access_rights(request.form, kwargs)
    util.pre_publication_action_check(username,
                                      mapname,
                                      kwargs,
                                      )

    util.patch_map(
        username,
        mapname,
        kwargs,
        'layman.map.filesystem.input_file' if file_changed else None
    )

    info = util.get_complete_map_info(username, mapname)

    return jsonify(info), 200


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>", methods=['DELETE'])
@util.lock_decorator
def delete_map(username, mapname):
    app.logger.info(f"DELETE Map, user={g.user}")

    # raise exception if map does not exist
    info = util.get_complete_map_info(cached=True)

    util.abort_map_tasks(username, mapname)

    util.delete_map(username, mapname)

    app.logger.info('DELETE Map done')

    return jsonify({
        'name': mapname,
        'url': info['url'],
        'uuid': info['uuid'],
    }), 200
