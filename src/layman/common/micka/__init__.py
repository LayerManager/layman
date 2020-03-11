import re

PROPERTIES = {
    'md_file_identifier': {
        'xpath': '/gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString/text()',
        'fn': lambda l: l[0] if l else None,
    },
    'md_date_stamp': {
        'xpath': '/gmd:MD_Metadata/gmd:dateStamp/gco:Date/text()',
        'fn': lambda l: l[0] if l else None,
    },
    'reference_system': {
        'xpath': '/gmd:MD_Metadata/gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor[starts-with(@xlink:href, "http://www.opengis.net/def/crs/EPSG/0/")]/text()',
        # 'fn': lambda l: l,
        'fn': lambda l: {li for li in l if re.match(r'^EPSG:\d+$', li)}
    },
}