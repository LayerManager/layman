from flask import Blueprint, jsonify, g, current_app as app, request

from layman.authn import authenticate, flush_cache
from layman.authn.util import login_required
from layman.authz import authorize
from .util import get_user_profile, reserve_username

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


@bp.route('', methods=['PATCH'])
@login_required
def patch():
    app.logger.info(f"PATCH Current User, user={g.user}")

    adjust_username = False
    if 'adjust_username' in request.args:
        adjust_username = request.args.get('adjust_username').lower() == 'true'

    username = request.form.get('username', '')

    # reserve username
    if adjust_username is True or len(username) > 0:
        reserve_username(username, adjust=adjust_username)

    user_profile = get_user_profile(g.user)

    return jsonify(user_profile), 200


@bp.route('', methods=['DELETE'])
@login_required
def delete():
    app.logger.info(f"DELETE Current User, user={g.user}")

    flush_cache()

    return jsonify({
        'message': 'Authentication cache flushed'
    }), 200
