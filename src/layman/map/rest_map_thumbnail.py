import os

from flask import Blueprint, send_file, current_app as app, g

from layman.common.filesystem.util import get_user_dir
from layman.http import LaymanError
from layman.util import check_username
from . import util
from .filesystem import thumbnail
from layman.authn import authenticate
from layman.authz import authorize


bp = Blueprint('rest_map_thumbnail', __name__)

@bp.before_request
@authenticate
@authorize
def before_request():
    pass


@bp.route('/maps/<mapname>/thumbnail', methods=['GET'])
def get(username, mapname):
    app.logger.info(f"GET Map Thumbnail, user={g.user}")

    # USER
    check_username(username)

    # MAP
    util.check_mapname(mapname)

    # raise exception if map does not exist
    util.get_complete_map_info(username, mapname)

    thumbnail_info = thumbnail.get_map_info(username, mapname)
    if thumbnail_info:
        userdir = get_user_dir(username)
        thumbnail_path = thumbnail_info['thumbnail']['path']
        thumbnail_path = os.path.join(userdir, thumbnail_path)
        return send_file(thumbnail_path, mimetype='image/png')

    raise LaymanError(16, {'mapname': mapname})


