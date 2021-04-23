from flask import Blueprint, jsonify, current_app as app, g

from layman import LaymanError, util as layman_util
from layman.util import check_username_decorator
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, MAP_REST_PATH_NAME

bp = Blueprint('rest_workspace_map_file', __name__)


@bp.before_request
@check_username_decorator
@util.check_mapname_decorator
@authenticate
@authorize_workspace_publications_decorator
@util.info_decorator
def before_request():
    pass


@bp.after_request
def after_request(response):
    layman_util.check_deprecated_url(response)
    return response


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>/file", methods=['GET'])
def get(workspace, mapname):
    app.logger.info(f"GET Map File, user={g.user}")

    map_json = util.get_map_file_json(workspace, mapname)

    if map_json is not None:
        return jsonify(map_json), 200

    raise LaymanError(27, {'mapname': mapname})
