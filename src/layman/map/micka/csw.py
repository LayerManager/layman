from datetime import datetime, date
from functools import partial
import os
import traceback
from xml.sax.saxutils import escape
from lxml import etree as ET
from requests.exceptions import HTTPError, ConnectionError
from flask import current_app

import crs as crs_def
from layman import common, settings, util as layman_util
from layman.common import language as common_language, empty_method, bbox as bbox_util
from layman.common.micka import util as common_util, requests as micka_requests
from layman.common.micka.util import get_metadata_uuid
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from layman.map.map_class import Map
from layman.util import url_for, get_publication_info

post_map = empty_method


def get_map_info(workspace, mapname, *, x_forwarded_items=None):
    uuid = layman_util.get_publication_uuid(workspace, MAP_TYPE, mapname)
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
                'record_url': common_util.get_metadata_url(uuid, url_type=common_util.RecordUrlType.BASIC),
                'comparison_url': url_for('rest_workspace_map_metadata_comparison.get', workspace=workspace, mapname=mapname,
                                          x_forwarded_items=x_forwarded_items),
            }
        }
    return {}


def delete_map(workspace, mapname):
    publication = Map(map_tuple=(workspace, mapname))
    return delete_map_by_class(publication)


def delete_map_by_class(publication: Map):
    muuid = common_util.get_metadata_uuid(publication.uuid)
    if muuid is None:
        return
    micka_requests.csw_delete(muuid)


def patch_map(workspace, mapname, metadata_properties_to_refresh=None, actor_name=None, create_if_not_exists=True,
              timeout=None):
    publication = Map(map_tuple=(workspace, mapname))
    return patch_map_by_class(publication, metadata_properties_to_refresh=metadata_properties_to_refresh,
                              actor_name=actor_name, create_if_not_exists=create_if_not_exists, timeout=timeout)


def patch_map_by_class(publication: Map, metadata_properties_to_refresh=None, actor_name=None,
                       create_if_not_exists=True, timeout=None):
    timeout = timeout or settings.DEFAULT_CONNECTION_TIMEOUT
    # current_app.logger.info(f"patch_map metadata_properties_to_refresh={metadata_properties_to_refresh}")
    metadata_properties_to_refresh = metadata_properties_to_refresh or []
    if len(metadata_properties_to_refresh) == 0:
        return {}
    csw = common_util.create_csw()
    if publication.uuid is None or csw is None:
        return None
    muuid = common_util.get_metadata_uuid(publication.uuid)
    element = common_util.get_record_element_by_id(csw, muuid)
    if element is None:
        if create_if_not_exists:
            return csw_insert(publication, actor_name=actor_name)
        return None
    # current_app.logger.info(f"Current element=\n{ET.tostring(element, encoding='unicode', pretty_print=True)}")

    _, prop_values = get_template_path_and_values(publication, http_method=common.REQUEST_METHOD_PATCH,
                                                  actor_name=actor_name)
    prop_values = {
        k: v for k, v in prop_values.items()
        if k in metadata_properties_to_refresh + ['md_date_stamp']
    }
    # current_app.logger.info(f"update_map prop_values={prop_values}")
    basic_template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), './record-template.xml')
    element = common_util.fill_xml_template_obj(element, prop_values, METADATA_PROPERTIES,
                                                basic_template_path=basic_template_path)
    record = ET.tostring(element, encoding='unicode', pretty_print=True)
    # current_app.logger.info(f"update_map record=\n{record}")
    micka_requests.csw_update({
        'muuid': muuid,
        'record': record,
    }, timeout=timeout)
    return muuid


def csw_insert(publication: Map, actor_name):
    template_path, prop_values = get_template_path_and_values(publication, http_method=common.REQUEST_METHOD_POST,
                                                              actor_name=actor_name)
    record = common_util.fill_xml_template_as_pretty_str(template_path, prop_values, METADATA_PROPERTIES)
    muuid = common_util.csw_insert({
        'record': record
    })
    return muuid


def map_layers_to_operates_on_layers(map_layers):
    used_uuids = set()
    operates_on = []
    for map_layer in map_layers:
        if not map_layer['uuid']:
            continue
        if map_layer['uuid'] not in used_uuids:
            operates_on.append(map_layer)
            used_uuids.add(map_layer['uuid'])
    return operates_on


def map_to_operates_on(publication: Map, operates_on_muuids_filter=None, editor=None):
    # Either caller know muuids or wants filter by editor, never both at the same time, at least one must be used
    assert (operates_on_muuids_filter is None) != (editor is None)
    operates_on_layers = map_layers_to_operates_on_layers(publication.map_layers)

    operates_on = []
    csw_url = settings.CSW_PROXY_URL
    for internal_layer in operates_on_layers:
        layer_workspace = internal_layer['workspace']
        layername = internal_layer['name']
        layer_muuid = get_metadata_uuid(internal_layer['uuid'])
        context = {'keys': ['title']}
        if operates_on_muuids_filter is not None:
            if layer_muuid not in operates_on_muuids_filter:
                continue
        else:
            context['actor_name'] = editor
        publ_info = get_publication_info(layer_workspace, LAYER_TYPE, layername, context=context)
        if not (layer_muuid and publ_info):
            continue
        layer_title = publ_info['title']
        layer_csw_url = f"{csw_url}?SERVICE=CSW&VERSION=2.0.2&REQUEST=GetRecordById&OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&ID={layer_muuid}#_{layer_muuid}"
        operates_on.append({
            'xlink:title': layer_title,
            'xlink:href': layer_csw_url,
        })
    return operates_on


def get_template_path_and_values(publication: Map, *, http_method=None, actor_name):
    assert http_method in [common.REQUEST_METHOD_POST, common.REQUEST_METHOD_PATCH]
    operates_on = map_to_operates_on(publication, editor=actor_name)
    publ_datetime = publication.created_at
    revision_date = datetime.now()
    native_bbox = publication.native_bounding_box
    crs = publication.native_crs
    if bbox_util.is_empty(native_bbox):
        native_bbox = crs_def.CRSDefinitions[crs].default_bbox
    extent = bbox_util.transform(native_bbox, crs_from=publication.native_crs, crs_to=crs_def.EPSG_4326)
    title = publication.title
    abstract = publication.description
    md_language = next(iter(common_language.get_languages_iso639_2(' '.join([
        title or '',
        abstract or '',
    ]))), None)

    prop_values = _get_property_values(
        workspace=publication.workspace,
        mapname=publication.name,
        uuid=publication.uuid,
        title=title,
        abstract=abstract or None,
        publication_date=publ_datetime.strftime('%Y-%m-%d'),
        revision_date=revision_date.strftime('%Y-%m-%d'),
        md_date_stamp=date.today().strftime('%Y-%m-%d'),
        identifier=url_for('rest_workspace_map.get', workspace=publication.workspace, mapname=publication.name),
        identifier_label=publication.name,
        extent=extent,
        crs_list=[crs],
        md_organisation_name=None,
        organisation_name=None,
        operates_on=operates_on,
        md_language=md_language,
    )
    if http_method == common.REQUEST_METHOD_POST:
        prop_values.pop('revision_date', None)
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'record-template.xml')
    return template_path, prop_values


def _get_property_values(
        workspace='browser',
        mapname='map',
        uuid='af238200-8200-1a23-9399-42c9fca53543',
        title='Administrativní členění Libereckého kraje',
        abstract=None,
        md_organisation_name=None,
        organisation_name=None,
        publication_date='2007-05-25',
        revision_date='2008-05-25',
        md_date_stamp='2007-05-25',
        identifier='http://www.env.cz/data/liberec/admin-cleneni',
        identifier_label='Liberec-AdminUnits',
        extent=None,  # west, south, east, north
        crs_list=None,
        operates_on=None,
        md_language=None,
):
    crs_list = crs_list or ['EPSG:3857']
    west, south, east, north = extent or [14.62, 50.58, 15.42, 50.82]
    extent = [max(west, -180), max(south, -90), min(east, 180), min(north, 90)]

    # list of dictionaries, possible keys are 'xlink:title', 'xlink:href', 'uuidref'
    operates_on = operates_on or []
    operates_on = [
        {
            a: v for a, v in item.items()
            if a in ['xlink:title', 'xlink:href', 'uuidref']
        }
        for item in operates_on
    ]

    result = {
        'md_file_identifier': common_util.get_metadata_uuid(uuid),
        'md_language': md_language,
        'md_date_stamp': md_date_stamp,
        'reference_system': crs_list,
        'title': title,
        'publication_date': publication_date,
        'revision_date': revision_date,
        'identifier': {
            'identifier': identifier,
            'label': identifier_label,
        },
        'abstract': abstract,
        'graphic_url': url_for('rest_workspace_map_thumbnail.get', workspace=workspace, mapname=mapname),
        'extent': extent,

        'map_endpoint': escape(url_for('rest_workspace_map.get', workspace=workspace, mapname=mapname)),
        'map_file_endpoint': escape(url_for('rest_workspace_map_file.get', workspace=workspace, mapname=mapname)),
        'operates_on': operates_on,
        'md_organisation_name': md_organisation_name,
        'organisation_name': organisation_name,
    }

    return result


from micka import NAMESPACES

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
        'xpath_extract_fn': lambda vals: f"EPSG:{vals[0].rsplit('/')[-1]}" if vals else None,
        'adjust_property_element': common_util.adjust_reference_system_info,
    },
    'title': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:title',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'publication_date': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="publication"]]',
        'xpath_extract': './gmd:CI_Date/gmd:date/gco:Date/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': partial(common_util.adjust_date_string_with_type, date_type='publication'),
    },
    'revision_date': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="revision"]]',
        'xpath_extract': './gmd:CI_Date/gmd:date/gco:Date/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': partial(common_util.adjust_date_string_with_type, date_type='revision'),
    },
    'identifier': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:identifier',
        'xpath_extract': './gmd:MD_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda vals: {
            'identifier': vals[0],
            'label': vals[0].getparent().text,
        } if vals else None,
        'adjust_property_element': common_util.adjust_identifier_with_label,
    },
    'abstract': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification',
        'xpath_property': './gmd:abstract',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'organisation_name': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty',
        'xpath_property': './gmd:organisationName',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'graphic_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification',
        'xpath_property': './gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString]',
        'xpath_extract': './gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': common_util.adjust_graphic_url,
    },
    'extent': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent',
        'xpath_property': './gmd:geographicElement[gmd:EX_GeographicBoundingBox]',
        'xpath_extract': './gmd:EX_GeographicBoundingBox/*/gco:Decimal/text()',
        'xpath_extract_fn': lambda vals: [float(vals[0]), float(vals[2]), float(vals[1]), float(vals[3])] if len(vals) == 4 else None,
        'adjust_property_element': common_util.adjust_extent,
    },
    'operates_on': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification',
        'xpath_property': './srv:operatesOn[@xlink:href]',
        'xpath_extract': './@xlink:href',
        'xpath_extract_fn': lambda vals: {
            'xlink:href': vals[0],
            'xlink:title': vals[0].getparent().get(f"{{{NAMESPACES['xlink']}}}title"),
        } if vals else None,
        'adjust_property_element': common_util.adjust_operates_on,
    },
    'map_endpoint': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link" and gmd:CI_OnlineResource/gmd:function/gmd:CI_OnLineFunctionCode/@codeListValue="information"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': partial(common_util.adjust_online_url, resource_protocol='WWW:LINK-1.0-http--link',
                                           online_function='information'),
    },
    'map_file_endpoint': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link" and gmd:CI_OnlineResource/gmd:function/gmd:CI_OnLineFunctionCode/@codeListValue="download"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda vals: vals[0] if vals else None,
        'adjust_property_element': partial(common_util.adjust_online_url, resource_protocol='WWW:LINK-1.0-http--link',
                                           online_function='download'),
    },
}


def get_metadata_comparison(map: Map):
    uuid = map.uuid
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
        'map_endpoint',
        'map_file_endpoint',
        'operates_on',
        'organisation_name',
        'publication_date',
        'reference_system',
        'revision_date',
        'title',
    ], METADATA_PROPERTIES)
    # current_app.logger.info(f"props:\n{json.dumps(props, indent=2)}")
    # current_app.logger.info(f"csw.request={csw.request}")
    url = csw.request.replace(settings.CSW_URL, settings.CSW_PROXY_URL)
    return {
        f"{url}": props
    }
