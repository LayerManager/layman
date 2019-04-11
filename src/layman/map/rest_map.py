from flask import Blueprint

from layman.http import LaymanError


bp = Blueprint('rest_map', __name__)


@bp.route('/maps/<mapname>', methods=['GET'])
def get(username, mapname):
    raise LaymanError(25)

