from flask import Blueprint, current_app as app, g, jsonify

from layman import util as layman_util
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, MAP_REST_PATH_NAME
from .map_class import Map

bp = Blueprint('rest_workspace_map_metadata_comparison', __name__)


@bp.before_request
@layman_util.check_workspace_name_decorator
@util.check_mapname_decorator
@authenticate
@authorize_workspace_publications_decorator
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}/<mapname>/metadata-comparison", methods=['GET'])
def get(workspace, mapname):
    app.logger.info(f"GET Map Metadata Comparison, actor={g.user}")

    publication = Map(map_tuple=(workspace, mapname))
    md_props = util.get_metadata_comparison(publication)

    return jsonify(md_props), 200
