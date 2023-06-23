from flask import Blueprint, g, request, current_app as app

from layman import settings
from layman.authn import authenticate, get_authn_username
from layman.authz import authorize_publications_decorator
from layman.common import rest as rest_common

bp = Blueprint('rest_publications', __name__)


@bp.before_request
@authenticate
@authorize_publications_decorator
def before_request():
    pass


@bp.route(f"/{settings.REST_PUBLICATIONS_PREFIX}", methods=['GET'])
def get():
    app.logger.info(f"GET Publications, actor={g.user}")

    actor = get_authn_username()
    return rest_common.get_publications(publication_type=None, actor=actor, request_args=request.args)
