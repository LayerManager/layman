from flask import Blueprint, current_app as app, g, jsonify

from layman import util as layman_util
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, LAYER_REST_PATH_NAME
from .layer_class import Layer

bp = Blueprint('rest_workspace_layer_metadata_comparison', __name__)


@bp.before_request
@layman_util.check_workspace_name_decorator
@util.check_layername_decorator
@authenticate
@authorize_workspace_publications_decorator
def before_request():
    pass


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>/metadata-comparison", methods=['GET'])
def get(workspace, layername):
    app.logger.info(f"GET Layer Metadata Comparison, actor={g.user}")

    layer = Layer(layer_tuple=(workspace, layername))
    md_props = util.get_metadata_comparison(layer)

    return jsonify(md_props), 200
