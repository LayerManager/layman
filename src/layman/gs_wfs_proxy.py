from urllib.parse import urljoin
import requests

from flask import Blueprint, g, current_app as app, request, Response

from layman.authn import authenticate, flush_cache
from layman.authz import authorize

from layman import settings

bp = Blueprint('gs_wfs_proxy_bp', __name__)


@bp.before_request
@authenticate
@authorize
def before_request():
    pass


#curl -X GET -H "Content-Type: application/json" "http://localhost:8000/rest/wfs-proxy"
@bp.route('', methods=['GET'])
def get():
    app.logger.info(f"GET WFS proxy, user={g.user}")

    resp = requests.request(
        method=request.method,
        url=urljoin(settings.LAYMAN_GS_URL, 'wfs?request=Transaction'),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response

    # res = json.dumps({"name" : "Růže, byť zvána jinak, voněla by stejně",
    #                   "složení" : "Kristýna, Jura, Jirka, Des, INDEX"})
    #
    # return jsonify(res), 200
