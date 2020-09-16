import io
import json
import traceback
import re
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests
from flask import g, current_app

from layman.layer.filesystem.input_sld import get_layer_file
from layman.http import LaymanError
from layman import settings, patch_mode
from . import headers_json
from . import wms

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def update_layer(username, layername, layerinfo):
    pass


def delete_layer(username, layername):
    style_url = urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                        username + '/styles/' + layername)
    r = requests.get(style_url + '.sld',
                     auth=settings.LAYMAN_GS_AUTH
                     )
    if r.status_code == 404:
        return {}
    else:
        r.raise_for_status()
    sld_file = io.BytesIO(r.content)

    r = requests.delete(style_url,
                        headers=headers_json,
                        auth=settings.LAYMAN_GS_AUTH,
                        params={
                            'purge': 'true',
                            'recurse': 'true',
                        }
                        )
    if r.status_code == 404:
        return {}
    else:
        r.raise_for_status()
    wms.clear_cache(username)
    return {
        'sld': {
            'file': sld_file
        }
    }


def get_layer_info(username, layername):
    url = settings.LAYMAN_GS_REST + f'workspaces/{username}/styles/{layername}.xml'
    print(f"Get layer url={url}")
    r = requests.get(url)
    print(f"Get layer r={r.status_code}, {r.text}")
    if r.status_code == 200:
        info = {
            'sld': {
                'url': url
            },
        }
    else:
        info = {}
    print(f"Get layer info={info}")
    return info


def get_layer_names(username):
    return []


def get_publication_names(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    return []


def get_publication_uuid(username, publication_type, publication_name):
    return None


def launder_attribute_name(attr_name):
    # https://github.com/OSGeo/gdal/blob/355b41831cd2685c85d1aabe5b95665a2c6e99b7/gdal/ogr/ogrsf_frmts/pgdump/ogrpgdumpdatasource.cpp#L129,L155
    return re.sub(r"['\-#]", '_', attr_name.lower())


def create_layer_style(username, layername):
    sld_file = get_layer_file(username, layername)
    # print('create_layer_style', sld_file)
    if sld_file is None:
        r = requests.get(
            urljoin(settings.LAYMAN_GS_REST_STYLES, 'generic.sld'),
            auth=settings.LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        sld_file = io.BytesIO(r.content)
    r = requests.post(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username + '/styles/'),
        data=json.dumps(
            {
                "style": {
                    "name": layername,
                    # "workspace": {
                    #     "name": "browser"
                    # },
                    "format": "sld",
                    # "languageVersion": {
                    #     "version": "1.0.0"
                    # },
                    "filename": layername + ".sld"
                }
            }
        ),
        headers=headers_json,
        auth=settings.LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    # app.logger.info(sld_file.read())

    tree = ET.parse(sld_file)
    root = tree.getroot()
    if 'version' in root.attrib and root.attrib['version'] == '1.1.0':
        sld_content_type = 'application/vnd.ogc.se+xml'
    else:
        sld_content_type = 'application/vnd.ogc.sld+xml'

    propertname_els = tree.findall('.//{http://www.opengis.net/ogc}PropertyName')
    for el in propertname_els:
        el.text = launder_attribute_name(el.text)

    sld_file = io.BytesIO()
    tree.write(
        sld_file,
        encoding=None,
        xml_declaration=True,
    )
    sld_file.seek(0)

    r = requests.put(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                username + '/styles/' + layername),
        data=sld_file.read(),
        headers={
            'Accept': 'application/json',
            'Content-type': sld_content_type,
        },
        auth=settings.LAYMAN_GS_AUTH
    )
    if r.status_code == 400:
        raise LaymanError(14, data=r.text)
    r.raise_for_status()
    r = requests.put(urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                             username + '/layers/' + layername),
                     data=json.dumps(
                         {
                             "layer": {
                                 "defaultStyle": {
                                     "name": username + ':' + layername,
                                     "workspace": username,
                                 },
                             }
                         }),
                     headers=headers_json,
                     auth=settings.LAYMAN_GS_AUTH
                     )
    # app.logger.info(r.text)
    r.raise_for_status()


def get_metadata_comparison(username, layername):
    pass
