from flask import Blueprint, jsonify, request
from flask import current_app as app

from layman.http import LaymanError
from layman.util import check_username
from . import util
from .filesystem import input_chunk


bp = Blueprint('rest_layer_chunk', __name__)

@bp.route("/layers/<layername>/chunk", methods=['POST'])
def post(username, layername):
    app.logger.info('POST Layer Chunk')

    # USER
    check_username(username)

    # LAYER
    util.check_layername(layername)

    total_chunks = request.form.get('resumableTotalChunks', type=int)
    if total_chunks > 999:
        raise LaymanError(2, {
            'parameter': 'resumableTotalChunks',
            'expected value': 'number from 0 to 999',
        })
    chunk_number = request.form.get('resumableChunkNumber', default=1,
                                            type=int)
    filename = request.form.get('resumableFilename', default='error',
                                         type=str)
    parameter_name = request.form.get('layman_original_parameter', default='error',
                                         type=str)
    chunk = request.files['file']

    input_chunk.save_layer_file_chunk(username, layername, parameter_name,
                                                     filename, chunk,
                                                     chunk_number, total_chunks)
    # time.sleep(5)

    return jsonify({
        'message': 'Chunk saved.'
    }), 200


@bp.route("/layers/<layername>/chunk", methods=['GET'])
def get(username, layername):
    app.logger.info('GET Layer Chunk')

    chunk_number = request.args.get('resumableChunkNumber', default=1,
                                            type=int)
    filename = request.args.get('resumableFilename', default='error',
                                         type=str)
    parameter_name = request.args.get('layman_original_parameter', default='error',
                                         type=str)

    chunk_exists = input_chunk.layer_file_chunk_exists(
        username, layername, parameter_name, filename, chunk_number)

    if chunk_exists:
        return jsonify({
            'message': 'Chunk exists.'
        }), 200
    else:
        return jsonify({
            'message': 'Chunk not found.'
        }), 404


