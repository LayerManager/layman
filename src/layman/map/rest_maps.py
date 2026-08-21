import json
import io

from flask import Blueprint, jsonify, request, g
from flask import current_app as app
from werkzeug.datastructures import FileStorage

from layman.http import LaymanError
from layman import authn, util as layman_util, uuid
from layman.authn import authenticate, get_authn_username
from layman.authz import authorize_publications_decorator, authorize
from layman.common import redis as redis_util, rest as rest_common
from layman.util import url_for
from layman.uuid import register_publication_uuid_to_redis
from . import util, MAP_TYPE, MAP_REST_PATH_NAME
from .filesystem import input_file
from .map_class import Map

bp = Blueprint('rest_maps', __name__)


@bp.before_request
@authenticate
@authorize_publications_decorator
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}", methods=['GET'])
def get():
    app.logger.info(f"GET Maps, actor={g.user}")

    actor = get_authn_username()
    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    workspace = layman_util.get_workspace_from_request(request.args, required=False)
    if workspace:
        authorize(workspace, MAP_TYPE, None, request.method, actor)
    return rest_common.get_publications(
        MAP_TYPE,
        actor,
        request_args=request.args,
        workspace=workspace,
        x_forwarded_items=x_forwarded_items,
    )


@bp.route(f"/{MAP_REST_PATH_NAME}", methods=['POST'])
def post():
    app.logger.info(f"POST Maps, actor={g.user}")
    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)

    actor_name = authn.get_authn_username()
    workspace = layman_util.get_workspace_from_request(request.form, required=True)
    authorize(workspace, MAP_TYPE, None, request.method, actor_name)

    # UUID
    input_uuid = request.form.get('uuid')
    input_uuid = input_uuid if input_uuid else None
    uuid.check_input_uuid(input_uuid)

    # FILE
    if 'file' in request.files and not request.files['file'].filename == '':
        file = request.files["file"]
    else:
        raise LaymanError(1, {'parameter': 'file'})
    file_json = util.check_file(file, x_forwarded_items=x_forwarded_items)

    # NAME
    unsafe_mapname = request.form.get('name', '')
    if len(unsafe_mapname) == 0:
        unsafe_mapname = input_file.get_unsafe_mapname(file_json)
    mapname = util.to_safe_map_name(unsafe_mapname)
    util.check_mapname(mapname)
    existing_uuid = layman_util.get_publication_uuid(workspace, MAP_TYPE, mapname)
    if existing_uuid:
        raise LaymanError(24, {'mapname': mapname})

    # TITLE
    if len(request.form.get('title', '')) > 0:
        title = request.form['title']
    elif len(file_json.get('title', '')) > 0:
        title = file_json['title']
    else:
        title = mapname

    # DESCRIPTION
    if len(request.form.get('description', '')) > 0:
        description = request.form['description']
    else:
        description = file_json.get('abstract', '')

    map = None
    try:
        map_result = {
            'name': mapname,
        }

        kwargs = {
            'title': title,
            'description': description,
            'actor_name': actor_name,
            'x_forwarded_headers': x_forwarded_items.headers,
        }

        rest_common.setup_post_access_rights(request.form, kwargs, actor_name)
        map = Map(map_tuple=(workspace, mapname), load=False)
        util.pre_publication_action_check(map, kwargs)
        # register map uuid
        uuid_str = register_publication_uuid_to_redis(workspace, MAP_TYPE, mapname, input_uuid)
        kwargs['uuid'] = uuid_str
        map = Map(uuid=uuid_str, map_tuple=(workspace, mapname), load=False)
        redis_util.create_lock(map, request.method)

        map_result.update({
            'uuid': uuid_str,
            'url': url_for('rest_map.get', uuid=uuid_str, x_forwarded_items=x_forwarded_items),
        })

        file = FileStorage(
            io.BytesIO(json.dumps(file_json).encode()),
            file.filename
        )
        input_file.save_map_files(uuid_str, [file])

        util.post_map(
            map,
            kwargs,
            'layman.map.filesystem.input_file'
        )
    except Exception as exception:
        try:
            if map and map.uuid and layman_util.is_publication_chain_ready(map):
                redis_util.unlock_publication(map.uuid)
        finally:
            if map and map.uuid:
                redis_util.unlock_publication(map.uuid)
        raise exception

    # app.logger.info('uploaded map '+mapname)
    return jsonify([map_result]), 200


@bp.route(f"/{MAP_REST_PATH_NAME}", methods=['DELETE'])
def delete():
    app.logger.info(f"DELETE Maps, actor={g.user}")

    actor_name = authn.get_authn_username()
    workspace = layman_util.get_workspace_from_request(request.args, required=True)
    authorize(workspace, MAP_TYPE, None, request.method, actor_name)

    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    infos = layman_util.delete_publications(
        workspace,
        MAP_TYPE,
        request.method,
        x_forwarded_items=x_forwarded_items,
    )

    return infos, 200
