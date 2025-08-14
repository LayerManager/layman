import json
import io

from flask import Blueprint, jsonify, request, current_app as app, g
from werkzeug.datastructures import FileStorage

from layman import LaymanError, authn, util as layman_util
from layman.common import rest as rest_util
from layman.util import check_uuid_decorator
from layman.authn import authenticate
from layman.authz import authorize_uuid_publication_decorator
from . import util, MAP_REST_PATH_NAME, MAP_TYPE, get_map_patch_keys
from .filesystem import input_file, thumbnail
from .map_class import Map

bp = Blueprint('rest_map', __name__)


@bp.before_request
@check_uuid_decorator
@authenticate
@authorize_uuid_publication_decorator(expected_publication_type=MAP_TYPE)
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}/<uuid>", methods=['GET'])
def get(uuid):
    app.logger.info(f"GET Map, actor={g.user}")

    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    info = util.get_complete_map_info_by_uuid(uuid, x_forwarded_items=x_forwarded_items)

    return jsonify(info), 200


@bp.route(f"/{MAP_REST_PATH_NAME}/<uuid>", methods=['PATCH'])
@util.uuid_lock_decorator
def patch(uuid):
    app.logger.info(f"PATCH Map, actor={g.user}")

    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    info = layman_util.get_publication_info_by_uuid(uuid, context={})

    if not info:
        raise LaymanError(26, {'uuid': uuid})

    old_map = Map(uuid=uuid)

    # FILE
    file = None
    file_json = {}
    if 'file' in request.files and not request.files['file'].filename == '':
        file = request.files["file"]
    if file is not None:
        file_json = util.check_file(file, x_forwarded_items=x_forwarded_items)

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

    publication = Map(uuid=uuid)
    props_to_refresh = util.get_same_or_missing_prop_names(publication)
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
        'uuid': uuid,
    }

    rest_util.setup_patch_access_rights(request.form, kwargs)
    util.pre_publication_action_check_by_uuid(uuid, kwargs)

    if file is not None:
        thumbnail.delete_map(old_map)
        file = FileStorage(
            io.BytesIO(json.dumps(file_json).encode()),
            file.filename
        )
        input_file.save_map_files(uuid, [file])

    new_map = old_map.clone(**{k: v for k, v in kwargs.items() if k in {'title', 'description', 'access_rights'}})
    util.patch_map(
        new_map,
        kwargs,
        'layman.map.filesystem.input_file' if file_changed else None
    )

    patch_keys = get_map_patch_keys()
    info = layman_util.get_publication_info_by_uuid(uuid, context={'keys': patch_keys, 'x_forwarded_items': x_forwarded_items})
    if info:
        info['url'] = layman_util.get_publication_url(info['type'], info['uuid'], x_forwarded_items=x_forwarded_items)
        info = {key: value for key, value in info.items() if key in patch_keys}

    return jsonify(info), 200


@bp.route(f"/{MAP_REST_PATH_NAME}/<uuid>", methods=['DELETE'])
@util.uuid_lock_decorator
def delete_map(uuid):
    app.logger.info(f"DELETE Map, actor={g.user}")
    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)

    # raise exception if map does not exist
    info = layman_util.get_publication_info_by_uuid(uuid, context={'x_forwarded_items': x_forwarded_items})

    util.abort_map_chain_by_uuid(uuid)

    map = Map(uuid=uuid)
    util.delete_map(map)

    app.logger.info('DELETE Map done')

    return jsonify({
        'url': layman_util.get_publication_url(info['type'], uuid, x_forwarded_items=x_forwarded_items),
        'uuid': uuid,
    }), 200
