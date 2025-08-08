from flask import Blueprint, Response, current_app as app, g

from layman import LaymanError
from layman.util import check_uuid_decorator
from layman.authn import authenticate
from layman.authz import authorize_uuid_publication_decorator
from layman.layer.geoserver import sld
from layman.layer.qgis import wms as qgis_wms
from layman import settings, util as layman_util
from . import LAYER_REST_PATH_NAME, LAYER_TYPE

bp = Blueprint('rest_layer_style', __name__)


@bp.before_request
@check_uuid_decorator
@authenticate
@authorize_uuid_publication_decorator(expected_publication_type=LAYER_TYPE)
def before_request():
    pass


@bp.route(f"/{LAYER_REST_PATH_NAME}/<uuid>/style", methods=['GET'])
def get(uuid):
    app.logger.info(f"GET Layer Style, actor={g.user}")

    info = layman_util.get_publication_info_by_uuid(uuid, context={'keys': ['style_type']})

    if not info:
        raise LaymanError(15, {'uuid': uuid})

    style_type = info['_style_type']
    result = None
    if style_type == 'sld':
        response = sld.get_style_response(uuid=uuid, auth=settings.LAYMAN_GS_AUTH)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = {key: value for (key, value) in response.headers.items() if key.lower() not in excluded_headers}

        final_response = Response(response.content,
                                  response.status_code,
                                  headers)
        result = final_response
    elif style_type == 'qml':
        response_qml = qgis_wms.get_style_qml(uuid)
        result = Response(response_qml, mimetype='application/x-qgis-layer-settings')
    return result
