import os
from flask import Blueprint, send_file, current_app as app, g

from layman import LaymanError, util as layman_util
from layman.util import check_workspace_name_decorator
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from layman.common.filesystem.util import get_workspace_dir
from . import util, MAP_REST_PATH_NAME
from .filesystem import thumbnail

bp = Blueprint('rest_workspace_map_thumbnail', __name__)


@bp.before_request
@check_workspace_name_decorator
@util.check_mapname_decorator
@authenticate
@authorize_workspace_publications_decorator
def before_request():
    pass


@bp.after_request
def after_request(response):
    layman_util.check_deprecated_url(response)
    return response


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>/thumbnail", methods=['GET'])
def get(workspace, mapname):
    app.logger.info(f"GET Map Thumbnail, actor={g.user}")

    thumbnail_info = thumbnail.get_map_info(workspace, mapname)
    if thumbnail_info:
        workspace_dir = get_workspace_dir(workspace)
        thumbnail_path = thumbnail_info['thumbnail']['path']
        thumbnail_path = os.path.join(workspace_dir, thumbnail_path)
        return send_file(thumbnail_path, mimetype='image/png')

    raise LaymanError(16, {'mapname': mapname})
