from flask import Blueprint, jsonify

bp = Blueprint('rest_tools', __name__)


@bp.route('/style-info', methods=['GET'])
def get_style_info():
    result = dict()
    return jsonify(result), 200
