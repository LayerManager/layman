from urllib.parse import urljoin
import requests

from flask import Blueprint, g, current_app as app, request, Response, jsonify

from layman.authn import authenticate, flush_cache
from layman.authz import authorize

from layman import settings

bp = Blueprint('gs_wfs_proxy_bp', __name__)


@bp.before_request
@authenticate
@authorize
def before_request():
    pass


# curl -X GET -H "Accept: text/xml" -H "Content-type: text/xml" --data-binary @wfs-proxy-test.xml "http://localhost:8000/rest/wfs-proxy"
@bp.route('', methods=['GET'])
def get():
    app.logger.info(f"GET WFS proxy, user={g.user}")

    username = 'wfs_proxy_test'
# TODO
# [x]    1. headers
# [x]    2. data
# [x]    3. cookies
# [x]    4. url
# [ ]    5. username
# [ ]    6. auth

    base_url = urljoin(settings.LAYMAN_GS_URL, username) + '/'
    url_path_wfs = urljoin(base_url, 'wfs?request=Transaction')

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection', 'host']
    headers = {key: value for (key, value) in request.headers if key.lower() not in excluded_headers}

    r = requests.post(url_path_wfs,
                      data=request.get_data(),
                      headers=headers,
                      auth=settings.LAYMAN_GS_AUTH,
                      cookies=request.cookies,
                      allow_redirects=False
                      )
    return r.text, r.status_code
