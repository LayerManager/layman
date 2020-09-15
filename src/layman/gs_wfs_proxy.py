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
from layman.layer import LAYER_TYPE
from layman.authz import util as authz


bp = Blueprint('gs_wfs_proxy_bp', __name__)


@bp.before_request
@authenticate
def before_request():
    pass


def ensure_wfs_t_attributes(binary_data):
    try:
        xml_tree = ET.XML(binary_data)
        version = xml_tree.get('version')[0:4]
        if version not in ["2.0.", "1.0.", "1.1."] or xml_tree.get('service').upper() != "WFS":
            app.logger.warning(f"WFS Proxy: only xml version 2.0, 1.1, 1.0 and WFS service are supported. Request "
                               f"only redirected. Version={xml_tree.get('version')}, service={xml_tree.get('service')}")
            return

        authz_module = authz.get_authz_module()
        attribs = set()
        for action in xml_tree:
            action_qname = ET.QName(action)
            if action_qname.localname in ('Insert', 'Replace'):
                extracted_attribs = extract_attributes_from_wfs_t_insert_replace(action, authz_module)
                attribs.update(extracted_attribs)
            elif action_qname.localname in ('Update'):
                extracted_attribs = extract_attributes_from_wfs_t_update(action,
                                                                         authz_module,
                                                                         xml_tree,
                                                                         major_version=version[0:1])
                attribs.update(extracted_attribs)

        app.logger.info(f"GET WFS check_xml_for_attribute attribs={attribs}")
        if attribs:
            created_attributes = db.ensure_attributes(attribs)
            if created_attributes:
                gs_reset(settings.LAYMAN_GS_AUTH)

    except BaseException as err:
        app.logger.warning(f"WFS Proxy: error={err}, trace={traceback.format_exc()}")


def extract_attributes_from_wfs_t_update(action, authz_module, xml_tree, major_version="2"):
    attribs = set()
    layer_qname = action.get('typeName').split(':')
    ws_namespace = layer_qname[0]
    ws_match = re.match(r"^(" + USERNAME_ONLY_PATTERN + ")$", ws_namespace)
    if ws_match:
        ws_name = ws_match.group(1)
    else:
        app.logger.warning(f"WFS Proxy: skipping due to wrong namespace name. Namespace={ws_namespace}")
        return attribs
    layer_name = layer_qname[1]
    layer_match = re.match(LAYERNAME_RE, layer_name)
    if not layer_match:
        app.logger.warning(f"WFS Proxy: skipping due to wrong layer name. Layer name={layer_name}")
        return attribs
    if not authz_module.can_i_edit(LAYER_TYPE, ws_name, layer_name):
        app.logger.warning(f"Can not edit. ws_namespace={ws_namespace}")
        return attribs
    value_ref_string = "Name" if major_version == "1" else "ValueReference"
    properties = action.xpath('wfs:Property/wfs:' + value_ref_string, namespaces=xml_tree.nsmap)
    for prop in properties:
        split_text = prop.text.split(':')
        # No namespace in element text
        if len(split_text) == 1:
            attrib_name = split_text[0]
        # There is namespace in element text
        elif len(split_text) == 2:
            if split_text[0] != ws_namespace:
                app.logger.warning(f"WFS Proxy: skipping due to different namespace in layer and in "
                                   f"property. Layer namespace={ws_namespace}, "
                                   f"property namespace={split_text[0]}")
                continue
            attrib_name = split_text[1]
        attrib_match = re.match(ATTRNAME_RE, attrib_name)
        if not attrib_match:
            app.logger.warning(f"WFS Proxy: skipping due to wrong attribute name. "
                               f"Property={attrib_name}")
            continue
        attribs.add((ws_name,
                     layer_name,
                     attrib_name))
    return attribs


def extract_attributes_from_wfs_t_insert_replace(action, authz_module):
    attribs = set()
    for layer in action:
        layer_qname = ET.QName(layer)
        ws_namespace = layer_qname.namespace
        ws_match = re.match(r"^http://(" + USERNAME_ONLY_PATTERN + ")$", ws_namespace)
        if ws_match:
            ws_name = ws_match.group(1)
        else:
            app.logger.warning(f"WFS Proxy: skipping due to wrong namespace name. Namespace={ws_namespace}")
            continue
        layer_name = layer_qname.localname
        layer_match = re.match(LAYERNAME_RE, layer_name)
        if not layer_match:
            app.logger.warning(f"WFS Proxy: skipping due to wrong layer name. Layer name={layer_name}")
            continue
        if not authz_module.can_i_edit(LAYER_TYPE, ws_name, layer_name):
            app.logger.warning(f"WFS Proxy: Can not edit. ws_namespace={ws_name}")
            continue
        for attrib in layer:
            attrib_qname = ET.QName(attrib)
            if attrib_qname.namespace != ws_namespace:
                app.logger.warning(f"WFS Proxy: skipping due to different namespace in layer and in "
                                   f"property. Layer namespace={ws_namespace}, "
                                   f"property namespace={attrib_qname.namespace}")
                continue
            attrib_name = attrib_qname.localname
            attrib_match = re.match(ATTRNAME_RE, attrib_name)
            if not attrib_match:
                app.logger.warning(f"WFS Proxy: skipping due to wrong property name. Property name={attrib_name}")
                continue
            attribs.add((ws_name,
                         layer_name,
                         attrib_name))
    return attribs


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
        ensure_wfs_t_attributes(data)
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
