import os

from flask import Blueprint, send_file, current_app as app, g

from layman.common.filesystem.util import get_user_dir
from layman.http import LaymanError
from layman.util import check_username_decorator
from . import util
from .filesystem import thumbnail
from layman.authn import authenticate
from layman.authz import authorize_decorator

bp = Blueprint('rest_map_thumbnail', __name__)


@bp.before_request
@authenticate
@authorize_decorator
@check_username_decorator
@util.check_mapname_decorator
@util.info_decorator
def before_request():
    pass


@bp.route('/maps/<mapname>/thumbnail', methods=['GET'])
def get(username, mapname):
    app.logger.info(f"GET Map Thumbnail, user={g.user}")

    thumbnail_info = thumbnail.get_map_info(username, mapname)
    if thumbnail_info:
        userdir = get_user_dir(username)
        thumbnail_path = thumbnail_info['thumbnail']['path']
        thumbnail_path = os.path.join(userdir, thumbnail_path)
        return send_file(thumbnail_path, mimetype='image/png')

    raise LaymanError(16, {'mapname': mapname})
