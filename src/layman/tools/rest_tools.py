from flask import Blueprint, jsonify
from werkzeug.datastructures import FileStorage

from layman.layer.filesystem import input_style

bp = Blueprint('rest_tools', __name__)


@bp.route('/style-info', methods=['GET'])
def get_style_info():
    filepath = 'test_tools/data/style/small_layer_external_circle.qml'
    with open(filepath, 'rb') as file:
        file_storage = FileStorage(file)
        detected_type = input_style.get_style_type_from_file_storage(file_storage).code
    external_files = input_style.get_external_files_from_qml_file(filepath)
    result = {'type': detected_type,
              'external_files': list(external_files)}
    return jsonify(result), 200
