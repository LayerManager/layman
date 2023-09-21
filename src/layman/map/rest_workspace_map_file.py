from flask import Blueprint, jsonify, current_app as app, g, request

from layman import LaymanError, util as layman_util
from layman.util import check_workspace_name_decorator
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, MAP_REST_PATH_NAME

bp = Blueprint('rest_workspace_map_file', __name__)


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


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>/file", methods=['GET'])
def get(workspace, mapname):
    app.logger.info(f"GET Map File, actor={g.user}")

    x_forwarded_prefix = layman_util.get_x_forwarded_items(request.headers)

    map_json = util.get_map_file_json(workspace, mapname, x_forwarded_prefix=x_forwarded_prefix)

    if map_json is not None:
        return jsonify(map_json), 200

    raise LaymanError(27, {'mapname': mapname})
