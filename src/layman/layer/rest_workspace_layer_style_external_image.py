import mimetypes
from flask import Blueprint, current_app as app, g, send_file

from layman import LaymanError
from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from layman.layer.filesystem import input_style
from layman.util import check_workspace_name_decorator
from layman import util as layman_util
from . import util, LAYER_REST_PATH_NAME

bp = Blueprint('rest_workspace_layer_style_external_image', __name__)


@bp.before_request
@check_workspace_name_decorator
@util.check_layername_decorator
@authenticate
@authorize_workspace_publications_decorator
@util.info_decorator
def before_request():
    pass


@bp.after_request
def after_request(response):
    layman_util.check_deprecated_url(response)
    return response


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>/style/external_images/<filename>", methods=['GET'])
def get(workspace, layername, filename):
    app.logger.info(f"GET Style External Image, actor={g.user}, workspace={workspace}, layername={layername}, filename={filename}")
    image_path = input_style.get_external_image_path(workspace, layername, filename)
    if image_path:
        mime_type, _ = mimetypes.guess_type(image_path)
        return send_file(image_path, mimetype=mime_type)

    raise LaymanError(27, {'workspace': workspace, 'layername': layername, 'filename': filename})
