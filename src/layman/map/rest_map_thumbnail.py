from flask import Blueprint, send_file
from layman import LaymanError
from layman.authn import authenticate
from layman.authz import authorize_uuid_publication_decorator
from layman.util import check_uuid_decorator
from . import MAP_REST_PATH_NAME, MAP_TYPE
from .filesystem import thumbnail

bp = Blueprint('rest_map_thumbnail', __name__)


@bp.before_request
@check_uuid_decorator
@authenticate
@authorize_uuid_publication_decorator(expected_publication_type=MAP_TYPE)
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}/<uuid>/thumbnail", methods=['GET'])
def get(uuid):
    thumbnail_info = thumbnail.get_map_info_by_uuid(uuid)
    if thumbnail_info:
        thumbnail_path = thumbnail_info['_thumbnail']['path']
        return send_file(thumbnail_path, mimetype='image/png')

    raise LaymanError(16, {'uuid': uuid})
