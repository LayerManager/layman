from flask import Blueprint, current_app as app, g, jsonify

from layman import util as layman_util
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, MAP_REST_PATH_NAME

bp = Blueprint('rest_workspace_map_metadata_comparison', __name__)


@bp.before_request
@layman_util.check_username_decorator
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


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>/metadata-comparison", methods=['GET'])
def get(username, mapname):
    app.logger.info(f"GET Map Metadata Comparison, user={g.user}")

    md_props = util.get_metadata_comparison(username, mapname)

    return jsonify(md_props), 200
