from datetime import datetime, date
import os
from functools import partial
import traceback
import logging
from requests.exceptions import HTTPError, ConnectionError
from lxml import etree as ET
from flask import current_app

import crs as crs_def
from db import util as db_util
from layman.common.filesystem.uuid import get_publication_uuid_file
from layman.common.micka import util as common_util, requests as micka_requests
from layman.common import language as common_language, empty_method, empty_method_returns_none, bbox as bbox_util
from layman.layer.prime_db_schema import table as prime_db_table
from layman.layer.filesystem import gdal
from layman.layer.filesystem.uuid import get_layer_uuid
from layman.layer import db
from layman.layer.geoserver import wms
from layman.layer.geoserver import wfs
from layman.layer import LAYER_TYPE
from layman import settings, patch_mode, LaymanError, common
from layman.util import url_for, get_publication_info

logger = logging.getLogger(__name__)
PATCH_MODE = patch_mode.NO_DELETE
get_publication_uuid = empty_method_returns_none
post_layer = empty_method


def get_layer_info(workspace, layername):
    uuid = get_layer_uuid(workspace, layername)
    try:
        csw = common_util.create_csw()
        if uuid is None or csw is None:
            return {}
        muuid = common_util.get_metadata_uuid(uuid)
        csw.getrecordbyid(id=[muuid], esn='brief')
    except HTTPError as exc:
        current_app.logger.info(f'traceback={traceback.format_exc()},\n'
                                f'response={exc.response.text},\n'
                                f'http_code={exc.response.status_code}')
        return {}
    except ConnectionError:
        current_app.logger.info(traceback.format_exc())
        return {}
    if muuid in csw.records:
        return {
            'metadata': {
                'identifier': muuid,
                'csw_url': settings.CSW_PROXY_URL,
                'record_url': common_util.get_metadata_url(uuid),
                'comparison_url': url_for('rest_workspace_layer_metadata_comparison.get', workspace=workspace, layername=layername),
            }
        }
    return {}


def patch_layer(workspace, layername, metadata_properties_to_refresh, _actor_name=None, create_if_not_exists=True, timeout=None):
    timeout = timeout or settings.DEFAULT_CONNECTION_TIMEOUT
    # current_app.logger.info(f"patch_layer metadata_properties_to_refresh={metadata_properties_to_refresh}")
    if len(metadata_properties_to_refresh) == 0:
        return None
    uuid = get_layer_uuid(workspace, layername)
    csw = common_util.create_csw()
    if uuid is None or csw is None:
        return None
    muuid = common_util.get_metadata_uuid(uuid)
    element = common_util.get_record_element_by_id(csw, muuid)
    if element is None:
        if create_if_not_exists:
            return csw_insert(workspace, layername)
        return None
    # current_app.logger.info(f"Current element=\n{ET.tostring(el, encoding='unicode', pretty_print=True)}")

    _, prop_values = get_template_path_and_values(workspace, layername, http_method=common.REQUEST_METHOD_PATCH)
    prop_values = {
        k: v for k, v in prop_values.items()
        if k in metadata_properties_to_refresh + ['md_date_stamp']
    }
    # current_app.logger.info(f"patch_layer prop_values={prop_values}")
    basic_template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), './record-template.xml')
    element = common_util.fill_xml_template_obj(element, prop_values, METADATA_PROPERTIES,
                                                basic_template_path=basic_template_path)
    record = ET.tostring(element, encoding='unicode', pretty_print=True)
    # current_app.logger.info(f"patch_layer record=\n{record}")
    micka_requests.csw_update({
        'muuid': muuid,
        'record': record,
    }, timeout=timeout)
    return muuid


def delete_layer(workspace, layername, *, backup_uuid=None):
    uuid = get_layer_uuid(workspace, layername) or backup_uuid
    if backup_uuid and uuid:
        assert backup_uuid == uuid
    muuid = common_util.get_metadata_uuid(uuid)
    if muuid is None:
        return
    micka_requests.csw_delete(muuid)


def csw_insert(workspace, layername):
    template_path, prop_values = get_template_path_and_values(workspace, layername, http_method='post')
    record = common_util.fill_xml_template_as_pretty_str(template_path, prop_values, METADATA_PROPERTIES)
    muuid = common_util.csw_insert({
        'record': record
    })
    return muuid


def get_template_path_and_values(workspace, layername, http_method):
    logger.info(f'get_template_path_and_values start calculating data for {workspace}:{layername}')
    assert http_method in [common.REQUEST_METHOD_POST, common.REQUEST_METHOD_PATCH]
    publ_info = get_publication_info(workspace, LAYER_TYPE, layername, context={
        'keys': ['title', 'native_bounding_box', 'native_crs', 'description', 'geodata_type', 'table_uri', 'wms'],
    })
    title = publ_info['title']
    abstract = publ_info.get('description')
    native_bbox = publ_info.get('native_bounding_box')
    crs = publ_info.get('native_crs')
    if bbox_util.is_empty(native_bbox):
        native_bbox = crs_def.CRSDefinitions[crs].default_bbox
    extent = bbox_util.transform(native_bbox, crs_from=crs, crs_to=crs_def.EPSG_4326)

    uuid_file_path = get_publication_uuid_file(LAYER_TYPE, workspace, layername)
    publ_datetime = datetime.fromtimestamp(os.path.getmtime(uuid_file_path))
    revision_date = datetime.now()
    md_language = next(iter(common_language.get_languages_iso639_2(' '.join([
        title or '',
        abstract or ''
    ]))), None)
    temporal_extent = publ_info['wms'].get('time', {}).get('values', [])

    geodata_type = publ_info.get('geodata_type')
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        table_uri = publ_info['_table_uri']
        table_name = table_uri.table
        conn_cur = db_util.get_connection_cursor(db_uri_str=table_uri.db_uri_str)
        try:
            languages = db.get_text_languages(table_uri.schema, table_name, table_uri.primary_key_column,
                                              conn_cur=conn_cur)
        except LaymanError:
            languages = []
        try:
            scale_denominator = db.guess_scale_denominator(table_uri.schema, table_name, table_uri.primary_key_column,
                                                           table_uri.geo_column, conn_cur=conn_cur)
        except LaymanError:
            scale_denominator = None
        spatial_resolution = {
            'scale_denominator': scale_denominator,
        }
        wfs_url = wfs.get_wfs_url(workspace, external_url=True)
    elif geodata_type == settings.GEODATA_TYPE_RASTER:
        languages = []
        bbox_sphere_size = prime_db_table.get_bbox_sphere_size(workspace, layername)
        distance_value = gdal.get_normalized_ground_sample_distance_in_m(workspace, layername,
                                                                         bbox_size=bbox_sphere_size)
        spatial_resolution = {
            'ground_sample_distance': {
                'value': distance_value,
                'uom': 'm',
            }
        }
        wfs_url = None
    else:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")

    west, south, east, north = extent
    extent = [max(west, -180), max(south, -90), min(east, 180), min(north, 90)]
    languages = languages or []

    prop_values = {
        'md_file_identifier': common_util.get_metadata_uuid(get_layer_uuid(workspace, layername)),
        'md_language': md_language,
        'md_date_stamp': date.today().strftime('%Y-%m-%d'),
        'reference_system': settings.LAYMAN_OUTPUT_SRS_LIST,
        'title': title,
        'publication_date': publ_datetime.strftime('%Y-%m-%d'),
        'identifier': {
            'identifier': url_for('rest_workspace_layer.get', workspace=workspace, layername=layername),
            'label': layername,
        },
        'abstract': abstract,
        'graphic_url': url_for('rest_workspace_layer_thumbnail.get', workspace=workspace, layername=layername),
        'extent': extent,
        'temporal_extent': temporal_extent,
        'wms_url': f"{wms.add_capabilities_params_to_url(wms.get_wms_url(workspace, external_url=True))}&LAYERS={layername}",
        'wfs_url': f"{wfs.add_capabilities_params_to_url(wfs_url)}&LAYERS={layername}" if wfs_url else None,
        'layer_endpoint': url_for('rest_workspace_layer.get', workspace=workspace, layername=layername),
        'spatial_resolution': spatial_resolution,
        'language': languages,
        'md_organisation_name': None,
        'organisation_name': None,
    }
    if http_method == common.REQUEST_METHOD_PATCH:
        prop_values['revision_date'] = revision_date.strftime('%Y-%m-%d')
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'record-template.xml')
    logger.info(f'get_template_path_and_values data calculated for {workspace}:{layername}')
    return template_path, prop_values


METADATA_PROPERTIES = {
    'md_file_identifier': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:fileIdentifier',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'md_language': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:language',
        'xpath_extract': './gmd:LanguageCode/@codeListValue',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_language,
    },
    'md_organisation_name': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty',
        'xpath_property': './gmd:organisationName',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'md_date_stamp': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:dateStamp',
        'xpath_extract': './gco:Date/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_date_string,
    },
    'reference_system': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:referenceSystemInfo[gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor[starts-with(@xlink:href, "http://www.opengis.net/def/crs/EPSG/0/")]]',
        'xpath_extract': './gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda vals: int(vals[0].rsplit('/')[-1]) if vals else None,
        'adjust_property_element': common_util.adjust_reference_system_info,
    },
    'title': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:title',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'publication_date': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="publication"]]',
        'xpath_extract': './gmd:CI_Date/gmd:date/gco:Date/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': partial(common_util.adjust_date_string_with_type, date_type='publication'),
    },
    'revision_date': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="revision"]]',
        'xpath_extract': './gmd:CI_Date/gmd:date/gco:Date/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': partial(common_util.adjust_date_string_with_type, date_type='revision'),
    },
    'identifier': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:identifier',
        'xpath_extract': './gmd:MD_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda vals: {
            'identifier': vals[0],
            'label': vals[0].getparent().text,
        } if vals else None,
        'adjust_property_element': common_util.adjust_identifier_with_label,
    },
    'abstract': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:abstract',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'organisation_name': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty',
        'xpath_property': './gmd:organisationName',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'graphic_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString]',
        'xpath_extract': './gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_graphic_url,
    },
    'spatial_resolution': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:spatialResolution',
        'xpath_extract': '.',
        'xpath_extract_fn': common_util.extract_spatial_resolution,
        'adjust_property_element': common_util.adjust_spatial_resolution,
    },
    'language': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:language',
        'xpath_extract': './gmd:LanguageCode/@codeListValue',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_language,
    },
    'extent': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent',
        'xpath_property': './gmd:geographicElement[gmd:EX_GeographicBoundingBox]',
        'xpath_extract': './gmd:EX_GeographicBoundingBox/*/gco:Decimal/text()',
        'xpath_extract_fn': lambda vals: [float(vals[0]), float(vals[2]), float(vals[1]), float(vals[3])] if len(vals) == 4 else None,
        'adjust_property_element': common_util.adjust_extent,
    },
    'temporal_extent': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent',
        'xpath_property': './gmd:temporalElement[gmd:EX_TemporalExtent/gmd:extent/gml:TimeInstant/gml:timePosition]',
        'xpath_extract': './gmd:EX_TemporalExtent/gmd:extent/gml:TimeInstant/gml:timePosition/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_temporal_element,
    },
    'wms_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': f'./gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WMS-{wms.VERSION}-http-get-capabilities"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': partial(common_util.adjust_online_url,
                                           resource_protocol=f'OGC:WMS-{wms.VERSION}-http-get-capabilities',
                                           online_function='download'),
    },
    'wfs_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': f'./gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WFS-{wfs.VERSION}-http-get-capabilities"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': partial(common_util.adjust_online_url,
                                           resource_protocol=f'OGC:WFS-{wfs.VERSION}-http-get-capabilities',
                                           online_function='download'),
    },
    'layer_endpoint': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': partial(common_util.adjust_online_url, resource_protocol='WWW:LINK-1.0-http--link',
                                           online_function='information'),
    },
}


def get_metadata_comparison(workspace, layername):
    uuid = get_layer_uuid(workspace, layername)
    csw = common_util.create_csw()
    if uuid is None or csw is None:
        return {}
    muuid = common_util.get_metadata_uuid(uuid)
    element = common_util.get_record_element_by_id(csw, muuid)
    if element is None:
        return {}

    # current_app.logger.info(f"xml\n{ET.tostring(el)}")

    props = common_util.parse_md_properties(element, [
        'abstract',
        'extent',
        'graphic_url',
        'identifier',
        'layer_endpoint',
        'language',
        'organisation_name',
        'publication_date',
        'revision_date',
        'reference_system',
        'spatial_resolution',
        'temporal_extent',
        'title',
        'wfs_url',
        'wms_url',
    ], METADATA_PROPERTIES)
    # current_app.logger.info(f"props:\n{json.dumps(props, indent=2)}")
    # current_app.logger.info(f"csw.request={csw.request}")
    url = csw.request.replace(settings.CSW_URL, settings.CSW_PROXY_URL)
    return {
        f"{url}": props
    }
