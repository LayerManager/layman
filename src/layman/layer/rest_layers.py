from flask import Blueprint, g, request
from flask import current_app as app

from layman import settings
from . import LAYER_TYPE, LAYER_REST_PATH_NAME
from layman.authn import authenticate, get_authn_username
from layman.authz import authorize_publications_decorator
from layman.common import rest as rest_common

bp = Blueprint('rest_layers', __name__)


@bp.before_request
@authenticate
@authorize_publications_decorator
def before_request():
    pass


@bp.route(f"/{LAYER_REST_PATH_NAME}", methods=['GET'])
def get():
    app.logger.info(f"GET Layers, user={g.user}")

    user = get_authn_username() or settings.ANONYM_USER
    return rest_common.get_publications(LAYER_TYPE, user, request_args=request.args)
