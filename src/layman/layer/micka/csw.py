from datetime import datetime, date
import os
from functools import partial
import traceback
import logging
from requests.exceptions import HTTPError, ConnectionError
from lxml import etree as ET
from flask import current_app

import crs as crs_def
from layman.common.micka import util as common_util, requests as micka_requests
from layman.common import language as common_language, empty_method, bbox as bbox_util
from layman.layer.layer_class import Layer
from layman.layer.prime_db_schema import table as prime_db_table
from layman.layer.filesystem import gdal
from layman.layer import db
from layman.layer.geoserver import wms
from layman.layer.geoserver import wfs
from layman import settings, patch_mode, LaymanError, common
from layman.util import url_for, get_publication_info_by_class

logger = logging.getLogger(__name__)
PATCH_MODE = patch_mode.NO_DELETE
post_layer = empty_method


def get_layer_info(workspace, layername, *, x_forwarded_items=None):
    layer = Layer(layer_tuple=(workspace, layername))
    try:
        csw = common_util.create_csw()
        if not layer or csw is None:
            return {}
        muuid = layer.micka_ids.id
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
                'record_url': common_util.get_metadata_url(layer.uuid, url_type=common_util.RecordUrlType.BASIC),
                'comparison_url': url_for('rest_workspace_layer_metadata_comparison.get', workspace=workspace, layername=layername,
                                          x_forwarded_items=x_forwarded_items),
            }
        }
    return {}


def patch_layer(workspace, layername, metadata_properties_to_refresh, _actor_name=None, create_if_not_exists=True, timeout=None):
    layer = Layer(layer_tuple=(workspace, layername))
    return patch_layer_by_class(layer, metadata_properties_to_refresh=metadata_properties_to_refresh,
                                actor_name=_actor_name, create_if_not_exists=create_if_not_exists, timeout=timeout)


# pylint: disable=unused-argument
def patch_layer_by_class(publication: Layer, *, metadata_properties_to_refresh, actor_name=None,
                         create_if_not_exists=True, timeout=None):
    timeout = timeout or settings.DEFAULT_CONNECTION_TIMEOUT
    # current_app.logger.info(f"patch_layer metadata_properties_to_refresh={metadata_properties_to_refresh}")
    if len(metadata_properties_to_refresh) == 0:
        return None
    csw = common_util.create_csw()
    if publication.uuid is None or csw is None:
        return None
    muuid = publication.micka_ids.id
    element = common_util.get_record_element_by_id(csw, muuid)
    if element is None:
        if create_if_not_exists:
            return csw_insert(publication)
        return None
    # current_app.logger.info(f"Current element=\n{ET.tostring(el, encoding='unicode', pretty_print=True)}")

    _, prop_values = get_template_path_and_values(publication, http_method=common.REQUEST_METHOD_PATCH)
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


def delete_layer(layer: Layer):
    muuid = layer.micka_ids.id
    if muuid is None:
        return
    micka_requests.csw_delete(muuid)


def csw_insert(publication: Layer):
    template_path, prop_values = get_template_path_and_values(publication, http_method='post')
    record = common_util.fill_xml_template_as_pretty_str(template_path, prop_values, METADATA_PROPERTIES)
    muuid = common_util.csw_insert({
        'record': record
    })
    return muuid


def get_template_path_and_values(publication: Layer, *, http_method):
    logger.info(f'get_template_path_and_values start calculating data for {publication.workspace}:{publication.name}')
    assert http_method in [common.REQUEST_METHOD_POST, common.REQUEST_METHOD_PATCH]
    publ_info = get_publication_info_by_class(publication, context={
        'keys': ['wms'],
    })
    title = publication.title
    abstract = publication.description
    native_bbox = publication.native_bounding_box
    crs = publication.native_crs
    if bbox_util.is_empty(native_bbox):
        native_bbox = crs_def.CRSDefinitions[crs].default_bbox
    extent = bbox_util.transform(native_bbox, crs_from=crs, crs_to=crs_def.EPSG_4326)

    publ_datetime = publication.created_at
    revision_date = datetime.now()
    md_language = next(iter(common_language.get_languages_iso639_2(' '.join([
        title or '',
        abstract or ''
    ]))), None)
    temporal_extent = publ_info['wms'].get('time', {}).get('values', None)

    geodata_type = publication.geodata_type
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        table_uri = publication.table_uri
        table_name = table_uri.table
        try:
            languages = db.get_text_languages(table_uri.schema, table_name, table_uri.primary_key_column,
                                              uri_str=table_uri.db_uri_str)
        except LaymanError:
            languages = []
        try:
            scale_denominator = db.guess_scale_denominator(table_uri.schema, table_name, table_uri.primary_key_column,
                                                           table_uri.geo_column, uri_str=table_uri.db_uri_str)
        except LaymanError:
            scale_denominator = None
        spatial_resolution = {
            'scale_denominator': scale_denominator,
        }
        wfs_url = wfs.get_wfs_url(external_url=True)
    elif geodata_type == settings.GEODATA_TYPE_RASTER:
        languages = []
        bbox_sphere_size = prime_db_table.get_bbox_sphere_size(publication.workspace, publication.name)
        distance_value = gdal.get_normalized_ground_sample_distance_in_m(publication.uuid, bbox_size=bbox_sphere_size)
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

    wfs_name = publication.gs_ids.wfs.name
    wms_name = publication.gs_ids.wms.name
    prop_values = {
        'md_file_identifier': publication.micka_ids.id,
        'md_language': md_language,
        'md_date_stamp': date.today().strftime('%Y-%m-%d'),
        'reference_system': settings.LAYMAN_OUTPUT_SRS_LIST,
        'title': title,
        'publication_date': publ_datetime.strftime('%Y-%m-%d'),
        'identifier': {
            'identifier': url_for('rest_workspace_layer.get', workspace=publication.workspace,
                                  layername=publication.name),
            'label': publication.name,
        },
        'abstract': abstract,
        'graphic_url': url_for('rest_workspace_layer_thumbnail.get', workspace=publication.workspace,
                               layername=publication.name),
        'extent': extent,
        'temporal_extent': temporal_extent,
        'wms_url': f"{wms.add_capabilities_params_to_url(wms.get_wms_url(external_url=True))}&LAYERS={wms_name}",
        'wfs_url': f"{wfs.add_capabilities_params_to_url(wfs_url)}&LAYERS={wfs_name}" if wfs_url else None,
        'layer_endpoint': url_for('rest_workspace_layer.get', workspace=publication.workspace,
                                  layername=publication.name),
        'spatial_resolution': spatial_resolution,
        'language': languages,
        'md_organisation_name': None,
        'organisation_name': None,
    }
    if http_method == common.REQUEST_METHOD_PATCH:
        prop_values['revision_date'] = revision_date.strftime('%Y-%m-%d')
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'record-template.xml')
    logger.info(f'get_template_path_and_values data calculated for {publication.workspace}:{publication.name}')
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


def get_metadata_comparison(layer: Layer):
    csw = common_util.create_csw()
    if not layer or csw is None:
        return {}
    muuid = layer.micka_ids.id
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
