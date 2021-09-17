from flask import Blueprint, jsonify, request

from layman.http import LaymanError
from layman.layer.filesystem import input_style

bp = Blueprint('rest_tools', __name__)


@bp.route('/style-info', methods=['GET'])
def get_style_info():
    supported_style_types = ['qml']

    style_file = None
    if 'style' in request.files and not request.files['style'].filename == '':
        style_file = request.files['style']
    if not style_file:
        raise LaymanError(1, {'parameter': 'style'})

    detected_type = input_style.get_style_type_from_file_storage(style_file).code
    if detected_type not in supported_style_types:
        raise LaymanError(2, {'parameter': 'style', 'supported_values': supported_style_types})

    external_files = input_style.get_external_files_from_qml_file(style_file)
    result = {'type': detected_type,
              'external_files': list(external_files)}
    return jsonify(result), 200
