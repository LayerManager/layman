from flask import Blueprint, jsonify, request

from layman.http import LaymanError
from layman.layer.filesystem import input_style

bp = Blueprint('rest_tools', __name__)


@bp.route('/style-info', methods=['POST'])
def post_style_info():
    supported_style_types_for_external_files = ['qml']

    style_file = None
    if 'style' in request.files and not request.files['style'].filename == '':
        style_file = request.files['style']
    if not style_file:
        raise LaymanError(1, {'parameter': 'style'})

    detected_type = input_style.get_style_type_from_file_storage(style_file).code
    result = {'type': detected_type, }
    if detected_type in supported_style_types_for_external_files:
        result['external_image_paths'] = dict()
        external_images = input_style.get_categorized_external_images_from_qml_file(style_file)
        for key, item in external_images.items():
            result['external_image_paths'][key] = list(item)
    return jsonify(result), 200
