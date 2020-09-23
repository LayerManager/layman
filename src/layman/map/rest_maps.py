import json
import io

from flask import Blueprint, jsonify, request, current_app as app, g
from werkzeug.datastructures import FileStorage

from layman.http import LaymanError
from layman.util import check_username_decorator, url_for
from . import util, MAP_TYPE
from .filesystem import input_file, uuid
from layman.authn import authenticate
from layman.authz import authorize
from layman.common import redis as redis_util

bp = Blueprint('rest_maps', __name__)


@bp.before_request
@authenticate
@authorize
@check_username_decorator
def before_request():
    pass


@bp.route('/maps', methods=['GET'])
def get(username):
    app.logger.info(f"GET Maps, user={g.user}")

    mapinfos = util.get_map_infos(username)

    infos = [
        {
            'name': name,
            'url': url_for('rest_map.get', mapname=name, username=name),
            'uuid': uuid.get_map_uuid(username, name),
        }
        for (name, info) in mapinfos.items()
    ]
    return jsonify(infos), 200


@bp.route('/maps', methods=['POST'])
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

    mapurl = url_for('rest_map.get', mapname=mapname, username=username)

    redis_util.lock_publication(username, MAP_TYPE, mapname, request.method)

    try:
        map_result = {
            'name': mapname,
            'url': mapurl,
        }

        # register map uuid
        uuid_str = uuid.assign_map_uuid(username, mapname)
        map_result.update({
            'uuid': uuid_str,
        })

        file = FileStorage(
            io.BytesIO(json.dumps(file_json).encode()),
            file.filename
        )
        input_file.save_map_files(
            username, mapname, [file])

        kwargs = {
            'title': title,
            'description': description,
        }

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
