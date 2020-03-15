from datetime import datetime, date
import os
import pathlib
import traceback

from flask import current_app

from layman.common.filesystem.uuid import get_publication_uuid_file
from layman.common.micka import util as common_util
from layman.layer.filesystem.uuid import get_layer_uuid
from layman.layer.geoserver.wms import get_wms_proxy
from layman.layer.geoserver.util import get_gs_proxy_base_url
from layman.layer import LAYER_TYPE
from layman import settings, patch_mode
from layman.util import url_for_external
from requests.exceptions import HTTPError, ConnectionError
from urllib.parse import urljoin
from xml.sax.saxutils import escape
from lxml import etree as ET


PATCH_MODE = patch_mode.NO_DELETE


def get_metadata_uuid(uuid):
    return f"m-{uuid}" if uuid is not None else None


def get_layer_info(username, layername):
    uuid = get_layer_uuid(username, layername)
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
            }
        }
    else:
        return {}


def get_layer_names(username):
    # TODO consider reading layer names from all Micka's metadata records by linkage URL
    return []


def update_layer(username, layername, layerinfo):
    # TODO implement patching layer
    pass


def get_publication_names(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    return []


def get_publication_uuid(username, publication_type, publication_name):
    return None


def delete_layer(username, layername):
    uuid = get_layer_uuid(username, layername)
    muuid = get_metadata_uuid(uuid)
    if muuid is None:
        return
    common_util.csw_delete(muuid)


def csw_insert(username, layername):
    template_path, prop_values = get_template_path_and_values(username, layername)
    record = common_util.fill_xml_template_as_pretty_str(template_path, prop_values, METADATA_PROPERTIES)
    muuid = common_util.csw_insert({
        'record': record
    })
    return muuid


def get_template_path_and_values(username, layername):
    wms = get_wms_proxy(username)
    wms_layer = wms.contents[layername]
    uuid_file_path = get_publication_uuid_file(LAYER_TYPE, username, layername)
    publ_datetime = datetime.fromtimestamp(os.path.getmtime(uuid_file_path))

    unknown_value = 'neznámá hodnota'
    prop_values = _get_property_values(
        username=username,
        layername=layername,
        uuid=get_layer_uuid(username, layername),
        title=wms_layer.title,
        abstract=wms_layer.abstract or None,
        publication_date=publ_datetime.strftime('%Y-%m-%d'),
        md_date_stamp=date.today().strftime('%Y-%m-%d'),
        identifier=url_for_external('rest_layer.get', username=username, layername=layername),
        identifier_label=layername,
        extent=wms_layer.boundingBoxWGS84,
        ows_url=urljoin(get_gs_proxy_base_url(), username + '/ows'),
        md_organisation_name=unknown_value if settings.CSW_ORGANISATION_NAME_REQUIRED else None,
        organisation_name=unknown_value if settings.CSW_ORGANISATION_NAME_REQUIRED else None,
    )
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'record-template.xml')
    return template_path, prop_values


def _get_property_values(
        username='browser',
        layername='layer',
        uuid='ca238200-8200-1a23-9399-42c9fca53542',
        title='CORINE - Krajinný pokryv CLC 90',
        abstract=None,
        md_organisation_name=None,
        organisation_name=None,
        publication_date='2007-05-25',
        md_date_stamp='2007-05-25',
        identifier='http://www.env.cz/data/corine/1990',
        identifier_label='MZP-CORINE',
        extent=None,  # w, s, e, n
        ows_url="http://www.env.cz/corine/data/download.zip",
        epsg_codes=None,
        scale_denominator=None,
        language=None,
):
    epsg_codes = epsg_codes or [3857, 4326]
    w, s, e, n = extent or [11.87, 48.12, 19.13, 51.59]
    extent = [max(w, -180), max(s, -90), min(e, 180), min(n, 90)]

    result = {
        'md_file_identifier': get_metadata_uuid(uuid),
        'md_date_stamp': md_date_stamp,
        'reference_system': epsg_codes,
        'title': title,
        'publication_date': publication_date,
        'identifier': {
            'identifier': identifier,
            'label': identifier_label,
        },
        'abstract': abstract,
        'graphic_url': url_for_external('rest_layer_thumbnail.get', username=username, layername=layername),
        'extent': extent,

        'wms_url': ows_url,
        'wfs_url': ows_url,
        'layer_endpoint': url_for_external('rest_layer.get', username=username, layername=layername),
        'scale_denominator': scale_denominator,
        'language': language,
        'md_organisation_name': md_organisation_name,
        'organisation_name': organisation_name,
    }

    return result


def _clear_el(el):
    el.attrib.clear()
    for child in list(el):
        el.remove(child)


def _add_unknown_reason(el):
    from layman.common.micka.util import NAMESPACES
    el.attrib[ET.QName(NAMESPACES['gco'], 'nilReason')] = 'unknown'


def _adjust_character_string(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(f"""<gco:CharacterString xmlns:gco="{NAMESPACES['gco']}">{escape(prop_value)}</gco:CharacterString>""")
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_integer(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(f"""<gco:Integer xmlns:gco="{NAMESPACES['gco']}">{escape(str(prop_value))}</gco:CharacterString>""")
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_date_string(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(f"""<gco:Date xmlns:gco="{NAMESPACES['gco']}">{escape(prop_value)}</gco:Date>""")
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_date_string_with_type(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:CI_Date xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gco="{NAMESPACES['gco']}">
    <gmd:date>
        <gco:Date>{escape(prop_value)}</gco:Date>
    </gmd:date>
    <gmd:dateType>
        <gmd:CI_DateTypeCode codeListValue="publication" codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode">publication</gmd:CI_DateTypeCode>
    </gmd:dateType>
</gmd:CI_Date>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_reference_system_info(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:MD_ReferenceSystem xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gmx="{NAMESPACES['gmx']}" xmlns:xlink="{NAMESPACES['xlink']}">
    <gmd:referenceSystemIdentifier>
        <gmd:RS_Identifier>
            <gmd:code>
                <gmx:Anchor xlink:href="http://www.opengis.net/def/crs/EPSG/0/{prop_value}">EPSG:{prop_value}</gmx:Anchor>
            </gmd:code>
        </gmd:RS_Identifier>
    </gmd:referenceSystemIdentifier>
</gmd:MD_ReferenceSystem>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_identifier_with_label(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    parser = ET.XMLParser(remove_blank_text=True)
    if prop_value is not None:
        identifier = prop_value['identifier']
        label = prop_value['label']
        child_el = ET.fromstring(f"""
<gmd:MD_Identifier xmlns:gmx="{NAMESPACES['gmx']}" xmlns:gmd="{NAMESPACES['gmd']}" xmlns:xlink="{NAMESPACES['xlink']}">
    <gmd:code>
        <gmx:Anchor xlink:href="{identifier}">{escape(label)}</gmx:Anchor>
    </gmd:code>
</gmd:MD_Identifier>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_graphic_url(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:MD_BrowseGraphic xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gco="{NAMESPACES['gco']}">
    <gmd:fileName>
        <gco:CharacterString>{escape(prop_value)}</gco:CharacterString>
    </gmd:fileName>
    <gmd:fileType>
        <gco:CharacterString>PNG</gco:CharacterString>
    </gmd:fileType>
</gmd:MD_BrowseGraphic>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_language(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(f"""<gmd:LanguageCode xmlns:gmd="{NAMESPACES['gmd']}" codeListValue=\"{prop_value}\" codeList=\"http://www.loc.gov/standards/iso639-2/\">{prop_value}</gmd:LanguageCode>""")
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_extent(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:EX_Extent xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gco="{NAMESPACES['gco']}">
    <gmd:geographicElement>
        <gmd:EX_GeographicBoundingBox>
            <gmd:westBoundLongitude>
                <gco:Decimal>{prop_value[0]}</gco:Decimal>
            </gmd:westBoundLongitude>
            <gmd:eastBoundLongitude>
                <gco:Decimal>{prop_value[2]}</gco:Decimal>
            </gmd:eastBoundLongitude>
            <gmd:southBoundLatitude>
                <gco:Decimal>{prop_value[1]}</gco:Decimal>
            </gmd:southBoundLatitude>
            <gmd:northBoundLatitude>
                <gco:Decimal>{prop_value[3]}</gco:Decimal>
            </gmd:northBoundLatitude>
        </gmd:EX_GeographicBoundingBox>
    </gmd:geographicElement>
</gmd:EX_Extent>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_wms_url(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:CI_OnlineResource xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gmx="{NAMESPACES['gmx']}" xmlns:xlink="{NAMESPACES['xlink']}">
    <gmd:linkage>
        <gmd:URL>{escape(prop_value)}</gmd:URL>
    </gmd:linkage>
    <gmd:protocol>
        <gmx:Anchor xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WMS-1.3.0">OGC:WMS-1.3.0</gmx:Anchor>
    </gmd:protocol>
     <gmd:function>
        <gmd:CI_OnLineFunctionCode codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_OnLineFunctionCode" codeListValue="download">download</gmd:CI_OnLineFunctionCode>
     </gmd:function>
</gmd:CI_OnlineResource>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_wfs_url(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:CI_OnlineResource xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gmx="{NAMESPACES['gmx']}" xmlns:xlink="{NAMESPACES['xlink']}">
    <gmd:linkage>
        <gmd:URL>{escape(prop_value)}</gmd:URL>
    </gmd:linkage>
    <gmd:protocol>
        <gmx:Anchor xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WFS-2.0.0">OGC:WFS-2.0.0</gmx:Anchor>
    </gmd:protocol>
     <gmd:function>
        <gmd:CI_OnLineFunctionCode codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_OnLineFunctionCode" codeListValue="download">download</gmd:CI_OnLineFunctionCode>
     </gmd:function>
</gmd:CI_OnlineResource>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def _adjust_layer_endpoint_url(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:CI_OnlineResource xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gmx="{NAMESPACES['gmx']}" xmlns:xlink="{NAMESPACES['xlink']}">
    <gmd:linkage>
        <gmd:URL>{escape(prop_value)}</gmd:URL>
    </gmd:linkage>
    <gmd:protocol>
        <gmx:Anchor xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link">WWW:LINK-1.0-http--link</gmx:Anchor>
    </gmd:protocol>
     <gmd:function>
        <gmd:CI_OnLineFunctionCode codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_OnLineFunctionCode" codeListValue="information">information</gmd:CI_OnLineFunctionCode>
     </gmd:function>
</gmd:CI_OnlineResource>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


METADATA_PROPERTIES = {
    'md_file_identifier': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:fileIdentifier',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_character_string,
    },
    'md_organisation_name': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty',
        'xpath_property': './gmd:organisationName',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_character_string,
    },
    'md_date_stamp': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:dateStamp',
        'xpath_extract': './gco:Date/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_date_string,
    },
    'reference_system': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:referenceSystemInfo[gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor[starts-with(@xlink:href, "http://www.opengis.net/def/crs/EPSG/0/")]]',
        'xpath_extract': './gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda l: int(l[0].rsplit('/')[-1]) if len(l) else None,
        'adjust_property_element': _adjust_reference_system_info,
    },
    'title': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:title',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_character_string,
    },
    'publication_date': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="publication"]]',
        'xpath_extract': './gmd:CI_Date/gmd:date/gco:Date/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_date_string_with_type,
    },
    'identifier': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:identifier',
        'xpath_extract': './gmd:MD_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda l: {
            'identifier': l[0],
            'label': l[0].getparent().text,
        } if l else None,
        'adjust_property_element': _adjust_identifier_with_label,
    },
    'abstract': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:abstract',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_character_string,
    },
    'organisation_name': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty',
        'xpath_property': './gmd:organisationName',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_character_string,
    },
    'graphic_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString]',
        'xpath_extract': './gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_graphic_url,
    },
    'scale_denominator': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction',
        'xpath_property': './gmd:denominator',
        'xpath_extract': './gco:Integer/text()',
        'xpath_extract_fn': lambda l: int(l[0]) if l else None,
        'adjust_property_element': _adjust_graphic_url,
    },
    'language': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:language',
        'xpath_extract': './gmd:LanguageCode/@codeListValue',
        'xpath_extract_fn': lambda l: int(l[0]) if l else None,
        'adjust_property_element': _adjust_language,
    },
    'extent': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:extent',
        'xpath_extract': './gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/*/gco:Decimal/text()',
        'xpath_extract_fn': lambda l: [float(l[0]), float(l[2]), float(l[1]), float(l[3])] if len(l) == 4 else None,
        'adjust_property_element': _adjust_extent,
    },
    'wms_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WMS-1.3.0"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_wms_url,
    },
    'wfs_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WFS-2.0.0"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_wfs_url,
    },
    'layer_endpoint': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': _adjust_layer_endpoint_url,
    },
}