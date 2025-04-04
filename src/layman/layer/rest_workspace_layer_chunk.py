import os

from flask import Blueprint, jsonify, request, current_app as app, g

from layman import LaymanError
from layman.util import check_workspace_name_decorator, get_publication_uuid
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from . import util, LAYER_REST_PATH_NAME
from .filesystem import input_chunk
from .filesystem.util import LAYER_TYPE

bp = Blueprint('rest_workspace_layer_chunk', __name__)


@bp.before_request
@check_workspace_name_decorator
@util.check_layername_decorator
@authenticate
@authorize_workspace_publications_decorator
def before_request():
    pass


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>/chunk", methods=['POST'])
def post(workspace, layername):
    app.logger.info(f"POST Layer Chunk, actor={g.user}")

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

    # log chunk size https://stackoverflow.com/a/23601025/5259610
    chunk_size = chunk.seek(0, os.SEEK_END)
    chunk.seek(0, os.SEEK_SET)
    app.logger.info(f"POST Layer Chunk, size = {chunk_size}")

    publ_uuid = get_publication_uuid(workspace, LAYER_TYPE, layername)
    input_chunk.save_layer_file_chunk(publ_uuid, parameter_name,
                                      filename, chunk,
                                      chunk_number, total_chunks)
    # time.sleep(5)

    return jsonify({
        'message': 'Chunk saved.'
    }), 200


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>/chunk", methods=['GET'])
def get(workspace, layername):
    app.logger.info(f"GET Layer Chunk, actor={g.user}")

    chunk_number = request.args.get('resumableChunkNumber', default=1,
                                    type=int)
    filename = request.args.get('resumableFilename', default='error',
                                type=str)
    parameter_name = request.args.get('layman_original_parameter', default='error',
                                      type=str)

    publ_uuid = get_publication_uuid(workspace, LAYER_TYPE, layername)
    chunk_exists = input_chunk.layer_file_chunk_exists(publ_uuid, parameter_name, filename, chunk_number)

    if chunk_exists:
        result = jsonify({
            'message': 'Chunk exists.'
        }), 200
    else:
        result = jsonify({
            'message': 'Chunk not found.'
        }), 404
    return result
