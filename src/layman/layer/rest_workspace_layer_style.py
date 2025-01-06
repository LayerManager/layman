from flask import Blueprint, current_app as app, g, Response

from layman.authn import authenticate
from layman.authz import authorize_workspace_publications_decorator
from layman.layer.geoserver import sld
from layman.layer.qgis import wms as qgis_wms
from layman.util import check_workspace_name_decorator
from layman import settings, util as layman_util
from . import util, LAYER_REST_PATH_NAME, LAYER_TYPE

bp = Blueprint('rest_workspace_layer_style', __name__)


@bp.before_request
@check_workspace_name_decorator
@util.check_layername_decorator
@authenticate
@authorize_workspace_publications_decorator
def before_request():
    pass


@bp.route(f"/{LAYER_REST_PATH_NAME}/<layername>/style", methods=['GET'])
def get(workspace, layername):
    app.logger.info(f"GET Style, actor={g.user}, workspace={workspace}, layername={layername}")

    style_type = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['style_type'], })['_style_type']
    result = None
    if style_type == 'sld':
        response = sld.get_style_response(workspace,
                                          layername,
                                          auth=settings.LAYMAN_GS_AUTH)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = {key: value for (key, value) in response.headers.items() if key.lower() not in excluded_headers}

        final_response = Response(response.content,
                                  response.status_code,
                                  headers)
        result = final_response
    elif style_type == 'qml':
        response_qml = qgis_wms.get_style_qml(workspace,
                                              layername,
                                              )
        result = Response(response_qml, mimetype='application/x-qgis-layer-settings')
    return result
