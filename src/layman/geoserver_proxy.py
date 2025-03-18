import re
import traceback
from collections import defaultdict

from urllib import parse
import requests
from requests.structures import CaseInsensitiveDict
from lxml import etree as ET

from flask import Blueprint, g, current_app as app, request, Response

import crs as crs_def
from geoserver.util import reset as gs_reset
from layman import authn, authz, settings, util as layman_util, LaymanError, names
from layman.authn import authenticate, is_user_with_name
from layman.layer import db
from layman.layer.layer_class import Layer
from layman.layer.qgis import wms as qgis_wms
from layman.layer.util import patch_after_feature_change
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
    result = (set(), set())
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
        layers.add(attrib[0])

    result = (attribs, layers)
    return result


def group_attributes_by_db(attribute_tuples):
    attrs_by_layer = defaultdict(list)
    for layer_uuid, attr in attribute_tuples:
        attrs_by_layer[layer_uuid].append(attr)

    attrs_by_db = defaultdict(list)
    for layer_uuid, attrs in attrs_by_layer.items():
        publ_info = layman_util.get_publication_info_by_uuid(uuid=layer_uuid, context={'keys': ['table_uri']})
        table_uri = publ_info['_table_uri']
        attrs_by_db[table_uri.db_uri_str].extend([
            (layer_uuid, attr, table_uri.schema, table_uri.table) for attr in attrs
        ])

    return attrs_by_db


def ensure_attributes_in_db(attributes_by_db):
    all_created_attr_tuples = set()
    for db_uri_str, attr_tuples in attributes_by_db.items():
        db_layman_attr_mapping = {
            (schema, table, attr): (layer_uuid, attr)
            for layer_uuid, attr, schema, table in attr_tuples
        }
        db_attr_tuples = list(db_layman_attr_mapping.keys())
        created_db_attr_tuples = db.ensure_attributes(db_attr_tuples, db_uri_str=db_uri_str)
        all_created_attr_tuples.update({db_layman_attr_mapping[a] for a in created_db_attr_tuples})
    return all_created_attr_tuples


def ensure_wfs_t_attributes(attribs):
    app.logger.info(f"ensure_wfs_t_attributes attribs={attribs}")
    editable_attribs = set(attr for attr in attribs if authz.can_i_edit(uuid=attr[0]))

    attrs_by_db = group_attributes_by_db(editable_attribs)
    all_created_attributes = ensure_attributes_in_db(attrs_by_db)

    if all_created_attributes:
        changed_layers = {layer_uuid for layer_uuid, _ in all_created_attributes}
        qgis_changed_layers = {
            layer_uuid for layer_uuid in changed_layers
            if layman_util.get_publication_info_by_uuid(layer_uuid, context={'keys': ['style_type'], }
                                                        )['_style_type'] == 'qml'
        }
        for layer_uuid in qgis_changed_layers:
            qgis_wms.save_qgs_file(layer_uuid)
        gs_reset(settings.LAYMAN_GS_AUTH)


def extract_layer_from_wfs_t_delete(action):
    _, layer_uuid = extract_layer_info_from_wfs_t_update_delete(action)
    return layer_uuid


def extract_layer_info_from_wfs_t_update_delete(action):
    result = (None, None)
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
    gs_layer_name = layer_qname[1]
    layer_uuid = names.geoserver_layername_to_uuid(geoserver_workspace=ws_name, geoserver_name=gs_layer_name)
    if not layer_uuid:
        app.logger.warning(f"WFS Proxy: wrong layer name. Layer name={gs_layer_name}")
        return result
    result = (ws_namespace, layer_uuid)
    return result


def extract_attributes_from_wfs_t_update(action, xml_tree, major_version="2"):
    attribs = set()
    ws_namespace, layer_uuid = extract_layer_info_from_wfs_t_update_delete(action)
    if not layer_uuid:
        return attribs
    value_ref_string = "Name" if major_version == "1" else "ValueReference"
    namespaces = xml_tree.nsmap
    if None in namespaces:
        namespaces['wfs'] = namespaces[None]
        namespaces.pop(None)
    properties = action.xpath('wfs:Property/wfs:' + value_ref_string, namespaces=namespaces)
    for prop in properties:
        split_text = prop.text.split(':')
        # No namespace in element text
        if len(split_text) == 1:
            attrib_name = split_text[0]
        # There is namespace in element text
        else:
            assert len(split_text) == 2
            if split_text[0] != ws_namespace:
                app.logger.warning(f"WFS Proxy: skipping due to different namespace in layer and in "
                                   f"property. Layer namespace={ws_namespace}, "
                                   f"property namespace={split_text[0]}")
                continue
            attrib_name = split_text[1]
        attribs.add((layer_uuid,
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
        gs_layer_name = layer_qname.localname
        layer_uuid = names.geoserver_layername_to_uuid(geoserver_workspace=ws_name, geoserver_name=gs_layer_name)
        if not layer_uuid:
            app.logger.warning(f"WFS Proxy: skipping due to wrong layer name. Layer name={gs_layer_name}")
            continue
        for attrib in layer:
            attrib_qname = ET.QName(attrib)
            if attrib_qname.namespace != ws_namespace:
                app.logger.warning(f"WFS Proxy: skipping due to different namespace in layer and in "
                                   f"property. Layer namespace={ws_namespace}, "
                                   f"property namespace={attrib_qname.namespace}")
                continue
            attrib_name = attrib_qname.localname
            attribs.add((layer_uuid,
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

    # adjust proxy base url headers
    for header in [
        'X-Forwarded-Proto',
        'X-Forwarded-Host',
        'X-Forwarded-For',
        'X-Forwarded-Path',
        'X-Forwarded-Prefix',
        'Forwarded',
        'Host',
    ]:
        headers_req.pop(header, None)
    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    headers_req['X-Forwarded-Proto'] = x_forwarded_items.proto or settings.LAYMAN_PUBLIC_URL_SCHEME
    headers_req['X-Forwarded-Host'] = x_forwarded_items.host or settings.LAYMAN_PROXY_SERVER_NAME
    headers_req['X-Forwarded-Path'] = x_forwarded_items.prefix or ''

    # ensure layer attributes in case of WFS-T
    app.logger.info(f"{request.method} GeoServer proxy, headers_req={headers_req}, url={url}")
    wfs_t_layers = set()
    if data is not None and len(data) > 0:
        try:
            wfs_t_attribs, wfs_t_layers = extract_attributes_and_layers_from_wfs_t(data)
            if wfs_t_attribs:
                ensure_wfs_t_attributes(wfs_t_attribs)
        except LaymanError as err:
            raise err
        except BaseException as err:
            app.logger.warning(f"WFS Proxy: error={err}, trace={traceback.format_exc()}")

    query_params = CaseInsensitiveDict(request.args.to_dict())

    # change CRS:84 to EPSG:4326 if one of SLD layers has native CRS EPSG:5514
    # otherwise layers are shifted by hundreds of meters, we are not sure about the reason
    if query_params.get('service') == 'WMS' and query_params.get('request') == 'GetMap'\
       and (query_params.get('crs') or query_params.get('srs')) == crs_def.CRS_84:
        layers = [layer.split(':') for layer in query_params.get('layers').split(',')]
        url_workspace = extract_workspace_from_url(subpath)
        layers = [layer if len(layer) == 2 else [url_workspace] + layer for layer in layers]
        fix_params = False
        for geoserver_workspace, layer in layers:
            uuid = names.geoserver_layername_to_uuid(geoserver_workspace=geoserver_workspace, geoserver_name=layer)
            publ_info = layman_util.get_publication_info_by_uuid(uuid=uuid, context={'keys': ['native_crs',
                                                                                              'style_type']})
            if publ_info and publ_info.get('native_crs') == crs_def.EPSG_5514 and publ_info.get('_style_type') == 'sld':
                fix_params = True
                break

        if fix_params:
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
                                allow_redirects=False,
                                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                                )

    if response.status_code == 200:
        for layer_uuid in wfs_t_layers:
            layer = Layer(uuid=layer_uuid)
            if authz.can_i_edit(uuid=layer_uuid) and layer.geodata_type == settings.GEODATA_TYPE_VECTOR:
                patch_after_feature_change(layer.workspace, layer.name)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = {key: value for (key, value) in response.headers.items() if key.lower() not in excluded_headers}

    final_response = Response(response.content,
                              response.status_code,
                              headers)
    return final_response
