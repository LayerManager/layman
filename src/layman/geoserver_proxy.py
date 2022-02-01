import re
import traceback

from urllib import parse
import requests
from requests.structures import CaseInsensitiveDict
from lxml import etree as ET

from flask import Blueprint, g, current_app as app, request, Response

import crs as crs_def
from geoserver.util import reset as gs_reset
from layman import authn, authz, settings, util as layman_util
from layman.authn import authenticate, is_user_with_name
from layman.layer import db, LAYER_TYPE
from layman.layer.geoserver import wms as gs_wms
from layman.layer.qgis import wms as qgis_wms
from layman.layer.util import LAYERNAME_PATTERN, ATTRNAME_PATTERN, patch_after_feature_change
from layman.util import WORKSPACE_NAME_ONLY_PATTERN


bp = Blueprint('geoserver_proxy_bp', __name__)


@bp.before_request
@authenticate
def before_request():
    pass


def extract_attributes_and_layers_from_wfs_t(binary_data):
    xml_tree = ET.XML(binary_data)
    version = xml_tree.get('version')[0:4]
    service = xml_tree.get('service').upper()
    attribs = set()
    layers = set()
    result = (attribs, layers)
    if service != 'WFS':
        return result
    if version not in ["2.0.", "1.0.", "1.1."]:
        app.logger.warning(f"WFS Proxy: only xml versions 2.0, 1.1, 1.0 are supported. Request "
                           f"only redirected. Version={xml_tree.get('version')}")
        return result

    for action in xml_tree:
        action_qname = ET.QName(action)
        if action_qname.localname in ('Insert', 'Replace',):
            extracted_attribs = extract_attributes_from_wfs_t_insert_replace(action)
            attribs.update(extracted_attribs)
        elif action_qname.localname in ('Update',):
            extracted_attribs = extract_attributes_from_wfs_t_update(action,
                                                                     xml_tree,
                                                                     major_version=version[0:1])
            attribs.update(extracted_attribs)
        elif action_qname.localname in ('Delete',):
            layer = extract_layer_from_wfs_t_delete(action)
            if layer:
                layers.add(layer)

    for attrib in attribs:
        layers.add(attrib[:2])

    result = (attribs, layers)
    return result


def ensure_wfs_t_attributes(attribs):
    app.logger.info(f"GET WFS check_xml_for_attribute attribs={attribs}")
    editable_attribs = set(attr for attr in attribs if authz.can_i_edit(LAYER_TYPE, attr[0], attr[1]))
    created_attributes = db.ensure_attributes(editable_attribs)
    if created_attributes:
        changed_layers = {(workspace, layer) for workspace, layer, _ in created_attributes}
        qgis_changed_layers = {(workspace, layer) for workspace, layer in changed_layers
                               if layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['style_type'], })['style_type'] == 'qml'}
        for workspace, layer in qgis_changed_layers:
            qgis_wms.save_qgs_file(workspace, layer)
        gs_reset(settings.LAYMAN_GS_AUTH)


def extract_layer_from_wfs_t_delete(action):
    _, ws_name, layer_name = extract_layer_info_from_wfs_t_update_delete(action)
    result = (ws_name, layer_name) if layer_name and ws_name else None
    return result


def extract_layer_info_from_wfs_t_update_delete(action):
    result = (None, None, None)
    layer_qname = action.get('typeName').split(':')
    ws_namespace = layer_qname[0]
    ws_match = re.match(r"^(" + WORKSPACE_NAME_ONLY_PATTERN + ")$", ws_namespace)
    if ws_match:
        ws_name = ws_match.group(1)
    else:
        if ws_namespace != 'http://www.opengis.net/ogc' and not ws_namespace.startswith('http://www.opengis.net/fes/'):
            app.logger.warning(
                f"WFS Proxy: wrong namespace name. Namespace={ws_namespace}, action={ET.QName(action)}")
        return result
    layer_name = layer_qname[1]
    layer_match = re.match(LAYERNAME_PATTERN, layer_name)
    if not layer_match:
        app.logger.warning(f"WFS Proxy: wrong layer name. Layer name={layer_name}")
        return result
    result = (ws_namespace, ws_name, layer_name)
    return result


def extract_attributes_from_wfs_t_update(action, xml_tree, major_version="2"):
    attribs = set()
    ws_namespace, ws_name, layer_name = extract_layer_info_from_wfs_t_update_delete(action)
    if not (layer_name and ws_name):
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
        attrib_match = re.match(ATTRNAME_PATTERN, attrib_name)
        if not attrib_match:
            app.logger.warning(f"WFS Proxy: skipping due to wrong attribute name. "
                               f"Property={attrib_name}")
            continue
        attribs.add((ws_name,
                     layer_name,
                     attrib_name))
    return attribs


def extract_attributes_from_wfs_t_insert_replace(action):
    attribs = set()
    for layer in action:
        layer_qname = ET.QName(layer)
        ws_namespace = layer_qname.namespace
        ws_match = re.match(r"^http://(" + WORKSPACE_NAME_ONLY_PATTERN + ")$", ws_namespace)
        if ws_match:
            ws_name = ws_match.group(1)
        else:
            if ws_namespace != 'http://www.opengis.net/ogc' and not ws_namespace.startswith('http://www.opengis.net/fes/'):
                app.logger.warning(f"WFS Proxy: skipping due to wrong namespace name. Namespace={ws_namespace}, action={ET.QName(action)}")
            continue
        layer_name = layer_qname.localname
        layer_match = re.match(LAYERNAME_PATTERN, layer_name)
        if not layer_match:
            app.logger.warning(f"WFS Proxy: skipping due to wrong layer name. Layer name={layer_name}")
            continue
        for attrib in layer:
            attrib_qname = ET.QName(attrib)
            if attrib_qname.namespace != ws_namespace:
                app.logger.warning(f"WFS Proxy: skipping due to different namespace in layer and in "
                                   f"property. Layer namespace={ws_namespace}, "
                                   f"property namespace={attrib_qname.namespace}")
                continue
            attrib_name = attrib_qname.localname
            attrib_match = re.match(ATTRNAME_PATTERN, attrib_name)
            if not attrib_match:
                app.logger.warning(f"WFS Proxy: skipping due to wrong property name. Property name={attrib_name}")
                continue
            attribs.add((ws_name,
                         layer_name,
                         attrib_name))
    return attribs


def extract_workspace_from_url(url):
    parts = url.split('/')
    workspace = parts[0] if len(parts) == 2 else None
    return workspace


@bp.route('/<path:subpath>', methods=['POST', 'GET'])
def proxy(subpath):
    app.logger.info(f"{request.method} GeoServer proxy, actor={g.user}, subpath={subpath}, url={request.url}, request.query_string={request.query_string.decode('UTF-8')}")

    # adjust authentication headers
    url = settings.LAYMAN_GS_URL + subpath
    query_params_string = request.query_string.decode('UTF-8')
    headers_req = {key.lower(): value for (key, value) in request.headers if key.lower() not in ['host', settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE.lower()]}
    data = request.get_data()
    authn_username = authn.get_authn_username()
    if is_user_with_name(authn_username):
        headers_req[settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE] = authn_username

    # ensure layer attributes in case of WFS-T
    app.logger.info(f"{request.method} GeoServer proxy, headers_req={headers_req}, url={url}")
    wfs_t_layers = set()
    if data is not None and len(data) > 0:
        try:
            wfs_t_attribs, wfs_t_layers = extract_attributes_and_layers_from_wfs_t(data)
            if wfs_t_attribs:
                ensure_wfs_t_attributes(wfs_t_attribs)
        except BaseException as err:
            app.logger.warning(f"WFS Proxy: error={err}, trace={traceback.format_exc()}")

    query_params = CaseInsensitiveDict(request.args.to_dict())

    # add buffer if incoming request is WMS GetMap in EPSG:3857 and one of SLD layers has native CRS EPSG:5514
    # otherwise features are missing in the response in this specific case, we are not sure about the reason
    if query_params.get('service') == 'WMS' and query_params.get('request') == 'GetMap'\
       and (query_params.get('crs') or query_params.get('srs')) in {crs_def.EPSG_3857, crs_def.CRS_84}:
        layers = [layer.split(':') for layer in query_params.get('layers').split(',')]
        url_workspace = extract_workspace_from_url(subpath)
        layers = [layer if len(layer) == 2 else [url_workspace] + layer for layer in layers]
        fix_params = False
        for geoserver_workspace, layer in layers:
            workspace = gs_wms.get_layman_workspace(geoserver_workspace)
            publ_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, {'keys': ['native_crs',
                                                                                                 'style_type']})
            if publ_info and publ_info.get('native_crs') == crs_def.EPSG_5514 and publ_info.get('style_type') == 'sld':
                fix_params = True
                break

        if fix_params:
            if (query_params.get('crs') or query_params.get('srs')) == crs_def.EPSG_3857:
                try:
                    width = float(query_params.get('width'))
                    minx, _, maxx, _ = [float(c) for c in query_params.get('bbox').split(',')]
                    resolution = (maxx - minx) / width
                    buffer_in_meters = 400  # hopefully it's enough for any case
                    buffer_in_pixels = round(buffer_in_meters / resolution)
                    buffer_request = int(query_params.get('buffer', 0))
                    if buffer_in_pixels > buffer_request:
                        query_params['buffer'] = buffer_in_pixels
                        query_params_string = parse.urlencode(query_params)
                except ValueError:
                    pass
            elif (query_params.get('crs') or query_params.get('srs')) == crs_def.CRS_84:
                if query_params.get('crs') == crs_def.CRS_84:
                    param_key = 'crs'
                    bbox = query_params['bbox'].split(',')
                    bbox = [bbox[1], bbox[0], bbox[3], bbox[2]]
                    query_params['bbox'] = ",".join(bbox)
                else:
                    param_key = 'srs'

                query_params[param_key] = crs_def.EPSG_4326
                query_params_string = parse.urlencode(query_params)

    url += '?' + query_params_string

    app.logger.info(f"{request.method} GeoServer proxy, final_url={url}")

    response = requests.request(method=request.method,
                                url=url,
                                data=data,
                                headers=headers_req,
                                cookies=request.cookies,
                                allow_redirects=False
                                )

    if response.status_code == 200:
        for workspace, layername in wfs_t_layers:
            file_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['file']})['file']
            if authz.can_i_edit(LAYER_TYPE, workspace, layername) and file_info['file_type'] == settings.FILE_TYPE_VECTOR:
                patch_after_feature_change(workspace, layername)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = {key: value for (key, value) in response.headers.items() if key.lower() not in excluded_headers}

    final_response = Response(response.content,
                              response.status_code,
                              headers)
    return final_response
