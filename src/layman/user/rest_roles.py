import logging
from flask import current_app as app, Blueprint, jsonify

from layman.authz.role_service import get_all_roles

logger = logging.getLogger(__name__)

bp = Blueprint('rest_roles', __name__)


@bp.route('', methods=['GET'])
def get():
    app.logger.info(f"GET Roles")

    roles = get_all_roles()

    return jsonify(roles), 200
