import re
import traceback

import requests
from lxml import etree as ET

from flask import Blueprint, g, current_app as app, request, Response

from layman.authn import authenticate
from layman import settings
from layman.layer import db
from layman.layer.util import LAYERNAME_RE, ATTRNAME_RE
from layman.util import USERNAME_ONLY_PATTERN
from layman.common.geoserver import reset as gs_reset


bp = Blueprint('gs_wfs_proxy_bp', __name__)


@bp.before_request
@authenticate
def before_request():
    pass


def check_xml_for_attribute(data_xml):
    try:
        xml_data = ET.XML(data_xml)
        if xml_data.get('version')[0:4] != "2.0." or xml_data.get('service').upper() != "WFS":
            app.logger.warning(f"WFS Proxy: only xml version 2.0 and WFS service are supported. Request only redirected. Version={xml_data.get('version')}, service={xml_data.get('service')}")
            return

        attribs = set()
        for action in xml_data:
            for layer in action:
                layer_qname = ET.QName(layer)
                ws_namespace = layer_qname.namespace
                ws_match = re.match(r"^http://(" + USERNAME_ONLY_PATTERN + ")$", ws_namespace)
                if ws_match:
                    ws_name = ws_match.group(1)
                else:
                    continue
                layer_name = layer_qname.localname
                layer_match = re.match(LAYERNAME_RE, layer_name)
                if not layer_match:
                    continue
                for attrib in layer:
                    attrib_qname = ET.QName(attrib)
                    if attrib_qname.namespace != layer_qname.namespace:
                        continue
                    attrib_name = attrib_qname.localname
                    attrib_match = re.match(ATTRNAME_RE, attrib_name)
                    if not attrib_match:
                        continue
                    attribs.add((ws_name,
                                 layer_name,
                                 attrib_name))

        app.logger.info(f"GET WFS check_xml_for_attribute attribs={attribs}")
        if attribs:
            db.ensure_attributes(attribs)
            gs_reset(settings.LAYMAN_GS_AUTH)

    except BaseException as err:
        app.logger.warning(f"WFS Proxy: error={err}, trace={traceback.format_exc()}")


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
