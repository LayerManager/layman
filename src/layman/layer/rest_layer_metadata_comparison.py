from flask import Blueprint, current_app as app, g, jsonify

from layman.authn import authenticate
from layman.authz import authorize_uuid_publication_decorator
from layman.util import check_uuid_decorator
from . import util, LAYER_REST_PATH_NAME, LAYER_TYPE
from .layer_class import Layer

bp = Blueprint('rest_layer_metadata_comparison', __name__)


@bp.before_request
@check_uuid_decorator
@authenticate
@authorize_uuid_publication_decorator(expected_publication_type=LAYER_TYPE)
def before_request():
    pass


@bp.route(f"/{LAYER_REST_PATH_NAME}/<uuid>/metadata-comparison", methods=['GET'])
def get(uuid):
    app.logger.info(f"GET Layer Metadata Comparison, actor={g.user}")

    md_props = util.get_metadata_comparison(Layer(uuid=uuid))

    return jsonify(md_props), 200
