from flask import Blueprint, jsonify, g

from layman.common.prime_db_schema import users
from layman.authn import authenticate
from layman import app

bp = Blueprint('rest_users', __name__)


@bp.before_request
@authenticate
def before_request():
    pass


@bp.route('', methods=['GET'])
def get():
    app.logger.info(f"GET Users, user={g.user}")

    user_infos = users.get_user_infos()
    infos = [
        {
            "username": username,
            "given_name": info.get("given_name"),
            "family_name": info.get("family_name"),
            "middle_name": info.get("middle_name"),
            "name": info.get("name"),
        }
        for username, info in user_infos.items()
    ]
    return jsonify(infos), 200
