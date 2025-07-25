from flask import Blueprint, jsonify, current_app as app, g, request

from layman import LaymanError, util as layman_util
from layman.util import check_uuid_decorator
from layman.authn import authenticate
from layman.authz import authorize_uuid_publication_decorator
from . import MAP_REST_PATH_NAME, MAP_TYPE
from .util import get_map_file_json

bp = Blueprint('rest_map_file', __name__)


@bp.before_request
@check_uuid_decorator
@authenticate
@authorize_uuid_publication_decorator(expected_publication_type=MAP_TYPE)
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}/<uuid>/file", methods=['GET'])
def get(uuid):
    app.logger.info(f"GET Map File, actor={g.user}")

    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    map_json = get_map_file_json(uuid, x_forwarded_items=x_forwarded_items)
    if map_json is not None:
        return jsonify(map_json), 200

    raise LaymanError(27, {'uuid': uuid})
