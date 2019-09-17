from flask import Blueprint, jsonify, g, current_app as app

from layman.authn import authenticate
from layman.authz import authorize
from .util import get_user_profile


bp = Blueprint('rest_current_user', __name__)

@bp.before_request
@authenticate
@authorize
def before_request():
    pass


@bp.route('', methods=['GET'])
def get():
    app.logger.info(f"GET Current User, user={g.user}")

    user_profile = get_user_profile(g.user)

    return jsonify(user_profile), 200
