import requests

from flask import Blueprint, g, current_app as app, request, Response

from layman.authn import authenticate
from layman import settings

bp = Blueprint('gs_wfs_proxy_bp', __name__)


@bp.before_request
@authenticate
def before_request():
    pass


@bp.route('/<path:subpath>', methods=['POST', 'GET'])
def proxy(subpath):
    app.logger.info(f"GET WFS proxy, user={g.user}, subppath={subpath}, url={request.url}, request.query_string={request.query_string.decode('UTF-8')}")

    url = settings.LAYMAN_GS_URL + subpath + '?' + request.query_string.decode('UTF-8')
    headers_req = {key.lower(): value for (key, value) in request.headers if key != 'Host'}
    if g.user is not None:
        headers_req[settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE] = g.user['username']

    app.logger.info(f"GET WFS proxy, headers_req={headers_req}, url={url}")
    response = requests.request(method=request.method,
                                url=url,
                                data=request.get_data(),
                                headers=headers_req,
                                cookies=request.cookies,
                                allow_redirects=False
                                )
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = {key: value for (key, value) in response.headers.items() if key.lower() not in excluded_headers}

    final_response = Response(response.content,
                              response.status_code,
                              headers)
    return final_response
