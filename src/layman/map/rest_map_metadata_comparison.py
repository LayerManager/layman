import os

from flask import Blueprint, send_file, current_app as app, g, jsonify

from layman.common.filesystem.util import get_user_dir
from layman.http import LaymanError
from layman.util import check_username_decorator
from . import util
from .filesystem import thumbnail
from layman.authn import authenticate
from layman.authz import authorize

bp = Blueprint('rest_map_metadata_comparison', __name__)


@bp.before_request
@authenticate
@authorize
@check_username_decorator
@util.check_mapname_decorator
@util.info_decorator
def before_request():
    pass


@bp.route('/maps/<mapname>/metadata-comparison', methods=['GET'])
def get(username, mapname):
    app.logger.info(f"GET Map Metadata Comparison, user={g.user}")

    md_props = util.get_metadata_comparison(username, mapname)

    return jsonify(md_props), 200
