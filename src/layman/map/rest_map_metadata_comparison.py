from flask import Blueprint, current_app as app, g, jsonify

from layman.authn import authenticate
from layman.authz import authorize_uuid_publication_decorator
from layman.util import check_uuid_decorator
from . import util, MAP_REST_PATH_NAME, MAP_TYPE
from .map_class import Map

bp = Blueprint('rest_map_metadata_comparison', __name__)


@bp.before_request
@check_uuid_decorator
@authenticate
@authorize_uuid_publication_decorator(expected_publication_type=MAP_TYPE)
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}/<uuid>/metadata-comparison", methods=['GET'])
def get(uuid):
    app.logger.info(f"GET Map Metadata Comparison, actor={g.user}")

    publication = Map(uuid=uuid)
    md_props = util.get_metadata_comparison(publication)

    return jsonify(md_props), 200
