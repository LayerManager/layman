from flask import Blueprint, g, request, current_app as app

from layman import settings
from layman.authn import authenticate, get_authn_username
from layman.authz import authorize_publications_decorator
from layman.common import rest as rest_common
from . import MAP_TYPE, MAP_REST_PATH_NAME

bp = Blueprint('rest_maps', __name__)


@bp.before_request
@authenticate
@authorize_publications_decorator
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}", methods=['GET'])
def get():
    app.logger.info(f"GET Maps, user={g.user}")

    user = get_authn_username() or settings.ANONYM_USER
    return rest_common.get_publications(MAP_TYPE, user, request_args=request.args)
