from flask import Blueprint, send_file
from flask import current_app as app

from .filesystem.util import get_user_dir
from layman.http import LaymanError
from layman.util import check_username
from layman.settings import *
from . import util
from .filesystem import thumbnail


bp = Blueprint('rest_layer_thumbnail', __name__)

@bp.route('/layers/<layername>/thumbnail', methods=['GET'])
def get(username, layername):
    app.logger.info('GET Layer Thumbnail')

    # USER
    check_username(username)

    # LAYER
    util.check_layername(layername)

    # raise exception if layer does not exist
    util.get_complete_layer_info(username, layername)

    thumbnail_info = thumbnail.get_layer_info(username, layername)
    if thumbnail_info:
        userdir = get_user_dir(username)
        thumbnail_path = thumbnail_info['thumbnail']['path']
        thumbnail_path = os.path.join(userdir, thumbnail_path)
        return send_file(thumbnail_path, mimetype='image/png')

    raise LaymanError(16, {'layername': layername})


