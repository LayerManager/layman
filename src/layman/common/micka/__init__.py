PROPERTIES = {
    'md_file_identifier': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:fileIdentifier',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
    'md_date_stamp': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:dateStamp',
        'xpath_extract': './gco:Date/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
    'reference_system': {
        'xpath_parent': '/gmd:MD_Metadata',
        'xpath_property': './gmd:referenceSystemInfo[gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor[starts-with(@xlink:href, "http://www.opengis.net/def/crs/EPSG/0/")]]',
        'xpath_extract': './gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda l: f"EPSG:{l[0].rsplit('/')[-1]}" if len(l) else None,
    },
    'title': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:title',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
    'publication_date': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="publication"]]',
        'xpath_extract': './gmd:CI_Date/gmd:date/gco:Date/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
    'identifier': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',
        'xpath_property': './gmd:identifier',
        'xpath_extract': './gmd:MD_Identifier/gmd:code/gmx:Anchor/@xlink:href',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
    'abstract': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:abstract',
        'xpath_extract': './gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
    'graphic_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString]',
        'xpath_extract': './gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
    'extent': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification',
        'xpath_property': './gmd:extent[gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox]',
        'xpath_extract': './gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/*/gco:Decimal/text()',
        'xpath_extract_fn': lambda l: [float(li) for li in l] if len(l) == 4 else None,
    },
    'wms_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WMS-1.3.0"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
    'wfs_url': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WFS-2.0.0"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
    'layer_endpoint': {
        'xpath_parent': '/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions',
        'xpath_property': './gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link"]',
        'xpath_extract': './gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()',
        'xpath_extract_fn': lambda l: l[0] if l else None,
    },
}