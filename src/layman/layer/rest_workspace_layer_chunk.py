from flask import Blueprint, jsonify, request, current_app as app, g

from layman import LaymanError, util as layman_util
from layman.util import check_username_decorator
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, LAYER_REST_PATH_NAME
from .filesystem import input_chunk

bp = Blueprint('rest_workspace_layer_chunk', __name__)


@bp.before_request
@check_username_decorator
@util.check_layername_decorator
@authenticate
@authorize_workspace_publications_decorator
def before_request():
    pass


@bp.after_request
def after_request(response):
    layman_util.check_deprecated_url(response)
    return response


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>/chunk", methods=['POST'])
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


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>/chunk", methods=['GET'])
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
        result = jsonify({
            'message': 'Chunk exists.'
        }), 200
    else:
        result = jsonify({
            'message': 'Chunk not found.'
        }), 404
    return result
