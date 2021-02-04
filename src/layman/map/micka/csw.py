from datetime import datetime, date, timedelta
from flask import current_app
from functools import partial
import json
import re
from requests.exceptions import HTTPError, ConnectionError
import os
import traceback
from xml.sax.saxutils import escape, quoteattr
from layman import settings, LaymanError
from layman.common.filesystem.uuid import get_publication_uuid_file
from layman.common import language as common_language
from layman.common.micka import util as common_util
from layman.map import MAP_TYPE
from layman.map.filesystem.uuid import get_map_uuid
from layman.map.filesystem.input_file import get_map_json, unquote_urls
from layman.layer.geoserver.util import get_gs_proxy_base_url
from layman.layer import LAYER_TYPE
from layman.util import url_for, USERNAME_ONLY_PATTERN, get_publication_info
from lxml import etree as ET


def get_metadata_uuid(uuid):
    return f"m-{uuid}" if uuid is not None else None


def get_map_info(username, mapname):
    uuid = get_map_uuid(username, mapname)
    try:
        csw = common_util.create_csw()
        if uuid is None or csw is None:
            return {}
        muuid = get_metadata_uuid(uuid)
        csw.getrecordbyid(id=[muuid], esn='brief')
    except (HTTPError, ConnectionError):
        current_app.logger.info(traceback.format_exc())
        return {}
    if muuid in csw.records:
        return {
            'metadata': {
                'identifier': muuid,
                'csw_url': settings.CSW_PROXY_URL,
                'record_url': settings.CSW_RECORD_URL.format(identifier=muuid),
                'comparison_url': url_for('rest_map_metadata_comparison.get', username=username, mapname=mapname),
            }
        }
    else:
        return {}


def get_publication_uuid(username, publication_type, publication_name):
    return None


def post_map(username, mapname):
    pass


def patch_map(username, mapname):
    pass


def delete_map(username, mapname):
    uuid = get_map_uuid(username, mapname)
    muuid = get_metadata_uuid(uuid)
    if muuid is None:
        return
    try:
        common_util.csw_delete(muuid)
    except (HTTPError, ConnectionError):
        current_app.logger.info(traceback.format_exc())
        raise LaymanError(38)


def post_map(username, mapname):
    pass


def patch_map(username, mapname, metadata_properties_to_refresh=None, actor_name=None):
    # current_app.logger.info(f"patch_map metadata_properties_to_refresh={metadata_properties_to_refresh}")
    metadata_properties_to_refresh = metadata_properties_to_refresh or []
    if len(metadata_properties_to_refresh) == 0:
        return {}
    uuid = get_map_uuid(username, mapname)
    csw = common_util.create_csw()
    if uuid is None or csw is None:
        return {}
    muuid = get_metadata_uuid(uuid)
    el = common_util.get_record_element_by_id(csw, muuid)
    if el is None:
        return csw_insert(username, mapname, actor_name=actor_name)
    # current_app.logger.info(f"Current element=\n{ET.tostring(el, encoding='unicode', pretty_print=True)}")

    _, prop_values = get_template_path_and_values(username, mapname, http_method='patch', actor_name=actor_name)
    prop_values = {
        k: v for k, v in prop_values.items()
        if k in metadata_properties_to_refresh + ['md_date_stamp']
    }
    # current_app.logger.info(f"update_map prop_values={prop_values}")
    basic_template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), './record-template.xml')
    el = common_util.fill_xml_template_obj(el, prop_values, METADATA_PROPERTIES,
                                           basic_template_path=basic_template_path)
    record = ET.tostring(el, encoding='unicode', pretty_print=True)
    # current_app.logger.info(f"update_map record=\n{record}")
    try:
        muuid = common_util.csw_update({
            'muuid': muuid,
            'record': record,
        })
    except (HTTPError, ConnectionError):
        current_app.logger.info(traceback.format_exc())
        raise LaymanError(38)
    return muuid


def csw_insert(username, mapname, actor_name):
    template_path, prop_values = get_template_path_and_values(username, mapname, http_method='post', actor_name=actor_name)
    record = common_util.fill_xml_template_as_pretty_str(template_path, prop_values, METADATA_PROPERTIES)
    try:
        muuid = common_util.csw_insert({
            'record': record
        })
    except (HTTPError, ConnectionError):
        current_app.logger.info(traceback.format_exc())
        raise LaymanError(38)
    return muuid


def map_json_to_operates_on(map_json, operates_on_muuids_filter=None, editor=None):
    # Either caller know muuids or wants filter by editor, never both at the same time
    assert not operates_on_muuids_filter or not editor
    unquote_urls(map_json)
    gs_url = get_gs_proxy_base_url()
    gs_url = gs_url if gs_url.endswith('/') else f"{gs_url}/"
    gs_wms_url_pattern = r'^' + re.escape(gs_url) + r'(' + USERNAME_ONLY_PATTERN + r')' + \
                         settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX + r'/(?:ows|wms|wfs).*$'
    layman_layer_names = []
    for map_layer in map_json['layers']:
        layer_url = map_layer.get('url', None)
        if not layer_url:
            continue
        # print(f"layer_url={layer_url}")
        match = re.match(gs_wms_url_pattern, layer_url)
        if not match:
            continue
        layer_username = match.group(1)
        if not layer_username:
            continue
        # print(f"layer_username={layer_username}")
        layer_names = [
            n for n in map_layer.get('params', {}).get('LAYERS', '').split(',')
            if len(n) > 0
        ]
        if not layer_names:
            continue
        for layername in layer_names:
            layman_layer_names.append((layer_username, layername))
    operates_on = []
    csw_url = settings.CSW_PROXY_URL
    for (layer_username, layername) in layman_layer_names:
        layer_md_info = get_publication_info(layer_username, LAYER_TYPE, layername, context={
            'sources_filter': 'layman.layer.micka.soap',
        })
        layer_muuid = layer_md_info.get('metadata', {}).get('identifier')
        if operates_on_muuids_filter is not None:
            if layer_muuid not in operates_on_muuids_filter:
                continue
            layer_wms_info = get_publication_info(layer_username, LAYER_TYPE, layername, context={
                'sources_filter': 'layman.layer.geoserver.wms',
            })
        else:
            layer_wms_info = get_publication_info(layer_username, LAYER_TYPE, layername, context={
                'sources_filter': 'layman.layer.geoserver.wms',
                'actor_name': editor,
            })
            if not (layer_muuid and layer_wms_info):
                continue
        layer_title = layer_wms_info['title']
        layer_csw_url = f"{csw_url}?SERVICE=CSW&VERSION=2.0.2&REQUEST=GetRecordById&OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&ID={layer_muuid}#_{layer_muuid}"
        operates_on.append({
            'xlink:title': layer_title,
            'xlink:href': layer_csw_url,
        })
    return operates_on


def map_json_to_epsg_codes(map_json):
    epsg_code = None
    proj_pattern = re.compile(r'^epsg:(\d+)$', re.IGNORECASE)
    proj_match = proj_pattern.match(map_json['projection'])
    if proj_match:
        epsg_code = int(proj_match.group(1))
    return [epsg_code] if epsg_code else None


def get_template_path_and_values(username, mapname, http_method=None, actor_name=None):
    assert http_method in ['post', 'patch']
    uuid_file_path = get_publication_uuid_file(MAP_TYPE, username, mapname)
    publ_datetime = datetime.fromtimestamp(os.path.getmtime(uuid_file_path))
    revision_date = datetime.now()
    map_json = get_map_json(username, mapname)
    operates_on = map_json_to_operates_on(map_json, editor=actor_name)
    md_language = next(iter(common_language.get_languages_iso639_2(' '.join([
        map_json['title'] or '',
        map_json['abstract'] or ''
    ]))), None)

    prop_values = _get_property_values(
        username=username,
        mapname=mapname,
        uuid=get_map_uuid(username, mapname),
        title=map_json['title'],
        abstract=map_json['abstract'] or None,
        publication_date=publ_datetime.strftime('%Y-%m-%d'),
        revision_date=revision_date.strftime('%Y-%m-%d'),
        md_date_stamp=date.today().strftime('%Y-%m-%d'),
        identifier=url_for('rest_map.get', username=username, mapname=mapname),
        identifier_label=mapname,
        extent=[float(c) for c in map_json['extent']],
        epsg_codes=map_json_to_epsg_codes(map_json),
        # TODO create config env variable to decide if to set organisation name or not
        md_organisation_name=None,
        organisation_name=None,
        operates_on=operates_on,
        md_language=md_language,
    )
    if http_method == 'post':
        prop_values.pop('revision_date', None)
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'record-template.xml')
    return template_path, prop_values


def _get_property_values(
        username='browser',
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
        extent=None,  # w, s, e, n
        epsg_codes=None,
        operates_on=None,
        md_language=None,
):
    epsg_codes = epsg_codes or ['3857']
    w, s, e, n = extent or [14.62, 50.58, 15.42, 50.82]
    extent = [max(w, -180), max(s, -90), min(e, 180), min(n, 90)]

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
        'md_file_identifier': get_metadata_uuid(uuid),
        'md_language': md_language,
        'md_date_stamp': md_date_stamp,
        'reference_system': epsg_codes,
        'title': title,
        'publication_date': publication_date,
        'revision_date': revision_date,
        'identifier': {
            'identifier': identifier,
            'label': identifier_label,
        },
        'abstract': abstract,
        'graphic_url': url_for('rest_map_thumbnail.get', username=username, mapname=mapname),
        'extent': extent,

        'map_endpoint': escape(url_for('rest_map.get', username=username, mapname=mapname)),
        'map_file_endpoint': escape(url_for('rest_map_file.get', username=username, mapname=mapname)),
        'operates_on': operates_on,
        'md_organisation_name': md_organisation_name,
        'organisation_name': organisation_name,
    }

    return result


from layman.common.micka.util import NAMESPACES

METADATA_PROPERTIES = {
    'md_file_identifier': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:fileIdentifier',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'md_language': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:language',
        'xpath_extract': './gmd:LanguageCode/@codeListValue',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': common_util.adjust_language,
    },
    'md_organisation_name': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty',
        'xpath_property': './gmd:organisationName',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'md_date_stamp': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:dateStamp',
        'xpath_extract': './gco:Date/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': common_util.adjust_date_string,
    },
    'reference_system': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:referenceSystemInfo[gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor[starts-with(@xlink:href, "http://www.opengis.net/def/crs/EPSG/0/")]]',
        'xpath_extract': './gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda l: int(l[0].rsplit('/')[-1]) if len(l) else None,
        'adjust_property_element': common_util.adjust_reference_system_info,
    },
    'title': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:title',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'publication_date': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="publication"]]',
        'xpath_extract': './gmd:CI_Date/gmd:date/gco:Date/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': partial(common_util.adjust_date_string_with_type, date_type='publication'),
    },
    'revision_date': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="revision"]]',
        'xpath_extract': './gmd:CI_Date/gmd:date/gco:Date/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': partial(common_util.adjust_date_string_with_type, date_type='revision'),
    },
    'identifier': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:identifier',
        'xpath_extract': './gmd:MD_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda l: {
            'identifier': l[0],
            'label': l[0].getparent().text,
        } if l else None,
        'adjust_property_element': common_util.adjust_identifier_with_label,
    },
    'abstract': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification',
        'xpath_property': './gmd:abstract',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'organisation_name': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty',
        'xpath_property': './gmd:organisationName',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': common_util.adjust_character_string,
    },
    'graphic_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification',
        'xpath_property': './gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString]',
        'xpath_extract': './gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': common_util.adjust_graphic_url,
    },
    'extent': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent',
        'xpath_property': './gmd:geographicElement[gmd:EX_GeographicBoundingBox]',
        'xpath_extract': './gmd:EX_GeographicBoundingBox/*/gco:Decimal/text()',
        'xpath_extract_fn': lambda l: [float(l[0]), float(l[2]), float(l[1]), float(l[3])] if len(l) == 4 else None,
        'adjust_property_element': common_util.adjust_extent,
    },
    'operates_on': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification',
        'xpath_property': './srv:operatesOn[@xlink:href]',
        'xpath_extract': './@xlink:href',
        'xpath_extract_fn': lambda l: {
            'xlink:href': l[0],
            'xlink:title': l[0].getparent().get(f"{{{NAMESPACES['xlink']}}}title"),
        } if l else None,
        'adjust_property_element': common_util.adjust_operates_on,
    },
    'map_endpoint': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link" and gmd:CI_OnlineResource/gmd:function/gmd:CI_OnLineFunctionCode/@codeListValue="information"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': partial(common_util.adjust_online_url, resource_protocol='WWW:LINK-1.0-http--link',
                                           online_function='information'),
    },
    'map_file_endpoint': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link" and gmd:CI_OnlineResource/gmd:function/gmd:CI_OnLineFunctionCode/@codeListValue="download"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': partial(common_util.adjust_online_url, resource_protocol='WWW:LINK-1.0-http--link',
                                           online_function='download'),
    },
}


def get_metadata_comparison(username, mapname):
    uuid = get_map_uuid(username, mapname)
    csw = common_util.create_csw()
    if uuid is None or csw is None:
        return {}
    muuid = get_metadata_uuid(uuid)
    el = common_util.get_record_element_by_id(csw, muuid)
    if el is None:
        return

    # current_app.logger.info(f"xml\n{ET.tostring(el)}")

    props = common_util.parse_md_properties(el, [
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
