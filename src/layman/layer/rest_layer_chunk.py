from flask import Blueprint, jsonify, request, current_app as app, g

from layman.http import LaymanError
from layman.util import check_username_decorator
from . import util
from .filesystem import input_chunk
from layman.authn import authenticate
from layman.authz import authorize

bp = Blueprint('rest_layer_chunk', __name__)


@bp.before_request
@authenticate
@authorize
@check_username_decorator
@util.check_layername_decorator
def before_request():
    pass


@bp.route("/layers/<layername>/chunk", methods=['POST'])
def post(username, layername):
    app.logger.info(f"POST Layer Chunk, user={g.user}")

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
    app.logger.info(f"GET Layer Chunk, user={g.user}")

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
