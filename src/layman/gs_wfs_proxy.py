from urllib.parse import urljoin
import requests

from flask import Blueprint, g, current_app as app, request, Response, jsonify

from layman.authn import authenticate, flush_cache
from layman.authz import authorize

from layman import settings

bp = Blueprint('gs_wfs_proxy_bp', __name__)


@bp.before_request
@authenticate
# @authorize
def before_request():
    pass


# curl -X GET -H "Accept: text/xml" -H "Content-type: text/xml" --data-binary @wfs-proxy-test.xml "http://localhost:8000/rest/wfs-proxy"
@bp.route('/<interface>', defaults={'username': None}, methods=['POST','GET'])
@bp.route('/<username>/<interface>', methods=['POST','GET'])
def proxy(username, interface):
    app.logger.info(f"GET WFS proxy, user={g.user}")

# TODO
# [x]    1. headers
# [x]    2. data
# [x]    3. cookies
# [x]    4. url
# [x]    5. username
# [ ]    6. auth

    url = request.url.replace(urljoin(request.host_url, '/rest/wfs-proxy/'), settings.LAYMAN_GS_URL)

    app.logger.info(f"GET WFS proxy, username={username}")
    app.logger.info(f"GET WFS proxy, interface={interface}")
    app.logger.info(f"GET WFS proxy, request.host_url={request.host_url}")
    app.logger.info(f"GET WFS proxy, request.url={request.url}")
    app.logger.info(f"GET WFS proxy, request.url_root={request.url_root}")
    app.logger.info(f"GET WFS proxy, request.base_url={request.base_url}")
    app.logger.info(f"GET WFS proxy, request.endpoint={request.endpoint}")
    app.logger.info(f"GET WFS proxy, request.host={request.host}")
    app.logger.info(f"GET WFS proxy, url={url}")

    response = requests.request(method=request.method,
                                url=url,
                                data=request.get_data(),
                                headers={key: value for (key, value) in request.headers if key != 'Host'},
                                auth=settings.LAYMAN_GS_AUTH,
                                cookies=request.cookies,
                                allow_redirects=False
                                )
    # excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    # headers = {key: value for (key, value) in response.headers if key.lower() not in excluded_headers}

    # response = Response(resp.content,
    #                     resp.status_code,
    #                     headers)
    # app.logger.info(f"GET WFS proxy, response.status_code={response.status_code}")
    # app.logger.info(f"GET WFS proxy, response.data={response.data}")
    return response.text, response.status_code
