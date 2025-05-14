from flask import Blueprint, send_file, current_app as app, g
import os

from layman import LaymanError
from layman.util import get_publication_info_by_uuid
from layman.authn import authenticate
from layman.authz import authorize_uuid_publications_decorator
from . import util, MAP_REST_PATH_NAME
from .util import check_uuid_decorator
from .filesystem import thumbnail

bp = Blueprint('rest_uuid_map_thumbnail', __name__)


@bp.before_request
@check_uuid_decorator
@authenticate
@authorize_uuid_publications_decorator
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}/<uuid>/thumbnail", methods=['GET'])
def get(uuid):
    info = get_publication_info_by_uuid(uuid, context={'keys': ['access_rights', 'workspace', 'type', 'name']})
    if not info:
        raise LaymanError(16, {'uuid': uuid})
    thumbnail_info = thumbnail.get_map_info_by_uuid(uuid, workspace=info['_workspace'], mapname=info['name'])
    if thumbnail_info:
        thumbnail_path = thumbnail_info['_thumbnail']['path']
        return send_file(thumbnail_path, mimetype='image/png')

    raise LaymanError(16, {'uuid': uuid})
