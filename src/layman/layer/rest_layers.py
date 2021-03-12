from flask import Blueprint, g
from flask import current_app as app

from layman import settings
from . import LAYER_TYPE, LAYER_REST_PATH_NAME
from layman.authn import authenticate
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

    user = g.user.get('username') if g.user else settings.ANONYM_USER
    return rest_common.get_publications(LAYER_TYPE, user)
