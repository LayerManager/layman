from flask import Blueprint, send_file, current_app as app, g

from layman import LaymanError
from layman.util import check_workspace_name_decorator
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, LAYER_REST_PATH_NAME
from .filesystem import thumbnail

bp = Blueprint('rest_workspace_layer_thumbnail', __name__)


@bp.before_request
@check_workspace_name_decorator
@util.check_layername_decorator
@authenticate
@authorize_workspace_publications_decorator
def before_request():
    pass


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>/thumbnail", methods=['GET'])
def get(workspace, layername):
    app.logger.info(f"GET Layer Thumbnail, actor={g.user}")

    thumbnail_info = thumbnail.get_layer_info(workspace, layername)
    if thumbnail_info:
        thumbnail_path = thumbnail_info['_thumbnail']['path']
        return send_file(thumbnail_path, mimetype='image/png')

    raise LaymanError(16, {'layername': layername})
