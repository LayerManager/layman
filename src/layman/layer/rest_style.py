import requests
from flask import Blueprint, current_app as app, g, Response

from layman.authn import authenticate
from layman import settings
from layman.layer.geoserver import sld

bp = Blueprint('rest_style_bp', __name__)

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}


@bp.before_request
@authenticate
def before_request():
    pass


@bp.route('/styles/<style_name>', methods=['GET'])
def get(username, style_name):
    app.logger.info(f"GET Style, user={g.user}, username={username}, style_name={style_name}")

    response = sld.get_style(username, style_name)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = {key: value for (key, value) in response.headers.items() if key.lower() not in excluded_headers}

    final_response = Response(response.content,
                              response.status_code,
                              headers)

    return final_response
