import os

from flask import Blueprint, send_file, current_app as app, g, jsonify

from layman.common.filesystem.util import get_user_dir
from layman.http import LaymanError
from layman.util import check_username_decorator
from . import util
from .filesystem import thumbnail
from layman.authn import authenticate
from layman.authz import authorize_publications_decorator

bp = Blueprint('rest_layer_metadata_comparison', __name__)


@bp.before_request
@check_username_decorator
@util.check_layername_decorator
@authenticate
@authorize_publications_decorator
@util.info_decorator
def before_request():
    pass


@bp.route('/layers/<layername>/metadata-comparison', methods=['GET'])
def get(username, layername):
    app.logger.info(f"GET Layer Metadata Comparison, user={g.user}")

    md_props = util.get_metadata_comparison(username, layername)

    return jsonify(md_props), 200
