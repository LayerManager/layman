from flask import Blueprint, current_app as app, g, Response

from layman.authn import authenticate
from layman.authz import authorize_publications_decorator
from layman.layer.geoserver import sld
from layman.layer.qgis import wms as qgis_wms
from layman.util import check_username_decorator
from layman import settings, util as layman_util
from . import util, LAYER_REST_PATH_NAME, LAYER_TYPE

bp = Blueprint('rest_layer_style', __name__)


@bp.before_request
@check_username_decorator
@util.check_layername_decorator
@authenticate
@authorize_publications_decorator
@util.info_decorator
def before_request():
    pass


@bp.after_request
def after_request(response):
    layman_util.check_deprecated_url(response)
    return response


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>/style", methods=['GET'])
def get(username, layername):
    app.logger.info(f"GET Style, user={g.user}, username={username}, layername={layername}")

    style_type = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={
        'sources_filter': layman_util.get_publication_types()[LAYER_TYPE]['access_rights_source'],
    })['style_type']
    if style_type == 'sld':
        response = sld.get_style_response(username,
                                          layername,
                                          auth=settings.LAYMAN_GS_AUTH)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = {key: value for (key, value) in response.headers.items() if key.lower() not in excluded_headers}

        final_response = Response(response.content,
                                  response.status_code,
                                  headers)
        return final_response
    elif style_type == 'qml':
        response_qml = qgis_wms.get_style_qml(username,
                                              layername,
                                              )
        return Response(response_qml, mimetype='application/x-qgis-layer-settings')
