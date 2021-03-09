import json
import io

from flask import Blueprint, jsonify, request, current_app as app, g
from werkzeug.datastructures import FileStorage

from layman.common import rest as rest_util
from layman.http import LaymanError
from layman.util import check_username_decorator, url_for
from . import util, MAP_TYPE, MAP_REST_PATH_NAME
from .filesystem import input_file, uuid
from layman import authn, util as layman_util
from layman.authn import authenticate
from layman.authz import authorize_publications_decorator
from layman.common import redis as redis_util

bp = Blueprint('rest_workspace_maps', __name__)


@bp.before_request
@check_username_decorator
@authenticate
@authorize_publications_decorator
def before_request():
    pass


@bp.after_request
def after_request(response):
    layman_util.check_deprecated_url(response)
    return response


@bp.route(f"/{MAP_REST_PATH_NAME}", methods=['GET'])
def get(username):
    app.logger.info(f"GET Maps, user={g.user}")

    mapinfos_whole = layman_util.get_publication_infos(username, MAP_TYPE)
    mapinfos = {name: info for (workspace, publication_type, name), info in mapinfos_whole.items()}

    sorted_infos = sorted(mapinfos.items(), key=lambda x: x[0])
    infos = [
        {
            'name': info["name"],
            'title': info.get("title", None),
            'url': url_for('rest_workspace_map.get', mapname=name, username=username),
            'uuid': info['uuid'],
            'access_rights': info['access_rights'],
        }
        for (name, info) in sorted_infos
    ]
    return jsonify(infos), 200


@bp.route(f"/{MAP_REST_PATH_NAME}", methods=['POST'])
def post(username):
    app.logger.info(f"POST Maps, user={g.user}")

    # FILE
    if 'file' in request.files and not request.files['file'].filename == '':
        file = request.files["file"]
    else:
        raise LaymanError(1, {'parameter': 'file'})
    file_json = util.check_file(file)

    # NAME
    unsafe_mapname = request.form.get('name', '')
    if len(unsafe_mapname) == 0:
        unsafe_mapname = input_file.get_unsafe_mapname(file_json)
    mapname = util.to_safe_map_name(unsafe_mapname)
    util.check_mapname(mapname)
    info = util.get_map_info(username, mapname)
    if info:
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

    mapurl = url_for('rest_workspace_map.get', mapname=mapname, username=username)

    redis_util.lock_publication(username, MAP_TYPE, mapname, request.method)

    try:
        map_result = {
            'name': mapname,
            'url': mapurl,
        }

        actor_name = authn.get_authn_username()

        kwargs = {
            'title': title,
            'description': description,
            'actor_name': actor_name
        }

        rest_util.setup_post_access_rights(request.form, kwargs, actor_name)
        util.pre_publication_action_check(username,
                                          mapname,
                                          kwargs,
                                          )
        # register map uuid
        uuid_str = uuid.assign_map_uuid(username, mapname)
        kwargs['uuid'] = uuid_str

        map_result.update({
            'uuid': uuid_str,
        })

        file = FileStorage(
            io.BytesIO(json.dumps(file_json).encode()),
            file.filename
        )
        input_file.save_map_files(
            username, mapname, [file])

        util.post_map(
            username,
            mapname,
            kwargs,
            'layman.map.filesystem.input_file'
        )
    except Exception as e:
        try:
            if util.is_map_task_ready(username, mapname):
                redis_util.unlock_publication(username, MAP_TYPE, mapname)
        finally:
            redis_util.unlock_publication(username, MAP_TYPE, mapname)
        raise e

    # app.logger.info('uploaded map '+mapname)
    return jsonify([map_result]), 200


@bp.route(f"/{MAP_REST_PATH_NAME}", methods=['DELETE'])
def delete(username):
    app.logger.info(f"DELETE Maps, user={g.user}")

    infos = layman_util.delete_publications(username,
                                            MAP_TYPE,
                                            29,
                                            util.is_map_task_ready,
                                            util.abort_map_tasks,
                                            util.delete_map,
                                            request.method,
                                            'rest_workspace_map.get',
                                            'mapname',
                                            )

    return infos, 200
