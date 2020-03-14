from lxml import etree as ET
from xml.sax.saxutils import escape


def clear_el(el):
    el.attrib.clear()
    for child in list(el):
        el.remove(child)


def add_unknown_reason(el):
    from layman.common.micka.util import NAMESPACES
    el.attrib[ET.QName(NAMESPACES['gco'], 'nilReason')] = 'unknown'


def adjust_character_string(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(f"""<gco:CharacterString xmlns:gco="{NAMESPACES['gco']}">{escape(prop_value)}</gco:CharacterString>""")
        prop_el.append(child_el)
    else:
        add_unknown_reason(prop_el)


def adjust_integer(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(f"""<gco:Integer xmlns:gco="{NAMESPACES['gco']}">{escape(str(prop_value))}</gco:CharacterString>""")
        prop_el.append(child_el)
    else:
        add_unknown_reason(prop_el)


def adjust_date_string(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(f"""<gco:Date xmlns:gco="{NAMESPACES['gco']}">{escape(prop_value)}</gco:Date>""")
        prop_el.append(child_el)
    else:
        add_unknown_reason(prop_el)


def adjust_date_string_with_type(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
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
        add_unknown_reason(prop_el)


def adjust_reference_system_info(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
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
        add_unknown_reason(prop_el)


def adjust_identifier_with_label(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
    if prop_value is not None:
        identifier = prop_value['identifier']
        label = prop_value['label']
        child_el = ET.fromstring(f"""<gmx:Anchor xmlns:gmx="{NAMESPACES['gmx']}" xmlns:xlink="{NAMESPACES['xlink']}" xlink:href="{identifier}">{escape(label)}</gmx:Anchor>""")
        prop_el.append(child_el)
    else:
        add_unknown_reason(prop_el)


def adjust_graphic_url(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
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
        add_unknown_reason(prop_el)


def adjust_language(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(f"""<gmd:LanguageCode xmlns:gmd="{NAMESPACES['gmd']}" codeListValue=\"{prop_value}\" codeList=\"http://www.loc.gov/standards/iso639-2/\">{prop_value}</gmd:LanguageCode>""")
        prop_el.append(child_el)
    else:
        add_unknown_reason(prop_el)


def adjust_extent(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
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
        add_unknown_reason(prop_el)


def adjust_wms_url(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
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
        add_unknown_reason(prop_el)


def adjust_wfs_url(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
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
        add_unknown_reason(prop_el)


def adjust_layer_endpoint_url(prop_el, prop_value):
    from layman.common.micka.util import NAMESPACES
    clear_el(prop_el)
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
        add_unknown_reason(prop_el)


PROPERTIES = {
    'md_file_identifier': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:fileIdentifier',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_character_string,
    },
    'md_organisation_name': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty',
        'xpath_property': './gmd:organisationName',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_character_string,
    },
    'md_date_stamp': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:dateStamp',
        'xpath_extract': './gco:Date/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_date_string,
    },
    'reference_system': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:referenceSystemInfo[gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor[starts-with(@xlink:href, "http://www.opengis.net/def/crs/EPSG/0/")]]',
        'xpath_extract': './gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda l: int(l[0].rsplit('/')[-1]) if len(l) else None,
        'adjust_property_element': adjust_reference_system_info,
    },
    'title': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:title',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_character_string,
    },
    'publication_date': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="publication"]]',
        'xpath_extract': './gmd:CI_Date/gmd:date/gco:Date/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_date_string_with_type,
    },
    'identifier': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:identifier',
        'xpath_extract': './gmd:MD_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda l: {
            'identifier': l[0],
            'label': l[0].getparent().text,
        } if l else None,
        'adjust_property_element': adjust_identifier_with_label,
    },
    'abstract': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:abstract',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_character_string,
    },
    'organisation_name': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty',
        'xpath_property': './gmd:organisationName',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_character_string,
    },
    'graphic_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString]',
        'xpath_extract': './gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_graphic_url,
    },
    'scale_denominator': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction',
        'xpath_property': './gmd:denominator',
        'xpath_extract': './gco:Integer/text()',
        'xpath_extract_fn': lambda l: int(l[0]) if l else None,
        'adjust_property_element': adjust_graphic_url,
    },
    'language': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:language',
        'xpath_extract': './gmd:LanguageCode/@codeListValue',
        'xpath_extract_fn': lambda l: int(l[0]) if l else None,
        'adjust_property_element': adjust_language,
    },
    'extent': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:extent',
        'xpath_extract': './gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/*/gco:Decimal/text()',
        'xpath_extract_fn': lambda l: [float(l[0]), float(l[2]), float(l[1]), float(l[3])] if len(l) == 4 else None,
        'adjust_property_element': adjust_extent,
    },
    'wms_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WMS-1.3.0"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_wms_url,
    },
    'wfs_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WFS-2.0.0"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_wfs_url,
    },
    'layer_endpoint': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
        'adjust_property_element': adjust_layer_endpoint_url,
    },
}