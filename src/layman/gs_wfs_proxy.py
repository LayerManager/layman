import requests
from lxml import etree as ET

from flask import Blueprint, g, current_app as app, request, Response

from layman.authn import authenticate
from layman import settings
from layman.layer import db

bp = Blueprint('gs_wfs_proxy_bp', __name__)


@bp.before_request
@authenticate
def before_request():
    pass


def check_xml_for_attribute(data_xml):
    xml_data = ET.XML(data_xml)
    attribs = set()
    for action in xml_data:
        for layer in action:
            for attrib in layer:
                # TODO getting username is not safe
                attribs.add((ET.QName(attrib).namespace,
                             ET.QName(layer).localname,
                             ET.QName(attrib).localname))

    app.logger.info(f"GET WFS check_xml_for_attribute attribs={attribs}")
    db.ensure_attributes(attribs)


@bp.route('/<path:subpath>', methods=['POST', 'GET'])
def proxy(subpath):
    app.logger.info(f"GET WFS proxy, user={g.user}, subpath={subpath}, url={request.url}, request.query_string={request.query_string.decode('UTF-8')}")

    url = settings.LAYMAN_GS_URL + subpath + '?' + request.query_string.decode('UTF-8')
    headers_req = {key.lower(): value for (key, value) in request.headers if key.lower() not in ['host', settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE.lower()]}
    data = request.get_data()
    if g.user is not None:
        headers_req[settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE] = g.user['username']

    app.logger.info(f"GET WFS proxy, headers_req={headers_req}, url={url}")
    if data is not None and len(data) > 0:
        check_xml_for_attribute(data)
    response = requests.request(method=request.method,
                                url=url,
                                data=data,
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
