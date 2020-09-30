from flask import Blueprint, current_app as app, g, Response

from layman.authn import authenticate
from layman.authz import authorize
from layman.layer.geoserver import sld
from layman.util import check_username_decorator
from layman import settings
from . import util

bp = Blueprint('rest_layer_style', __name__)



@bp.before_request
@authenticate
@authorize
@check_username_decorator
@util.check_layername_decorator
@util.info_decorator
def before_request():
    pass


@bp.route('/layers/<layername>/style', methods=['GET'])
def get(username, layername):
    app.logger.info(f"GET Style, user={g.user}, username={username}, layername={layername}")

    response = sld.get_style_response(username,
                                      layername,
                                      auth=settings.LAYMAN_GS_AUTH)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = {key: value for (key, value) in response.headers.items() if key.lower() not in excluded_headers}

    final_response = Response(response.content,
                              response.status_code,
                              headers)

    return final_response
