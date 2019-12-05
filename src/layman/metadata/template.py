from flask import url_for


def get_layer_values(
        uuid='ca238200-8200-1a23-9399-42c9fca53542',
        epsg_codes=None,
        title='CORINE - Krajinný pokryv CLC 90',
        date='2007-05-25',
        date_type='revision',
        data_identifier='http://www.env.cz/data/corine/1990',
        data_identifier_label='MZP-CORINE',
        abstract=None,
        username='browser',
        layername='layer',
        extent=None,
        ows_url="http://www.env.cz/corine/data/download.zip",
        scale_denominator=None,
        dataset_language=None,
):
    epsg_codes = epsg_codes or ['3857', '4326']
    extent = extent or [11.87, 19.13, 48.12, 51.59]

    result = {
        ###############################################################################################################
        # KNOWN TO LAYMAN
        ###############################################################################################################

        # layer UUID with prefix "m"
        'file_identifier': f"m{uuid}",

        'reference_system': ' '.join([
f"""
<gmd:referenceSystemInfo>
    <gmd:MD_ReferenceSystem>
        <gmd:referenceSystemIdentifier>
            <gmd:RS_Identifier>
                <gmd:code>
                    <gmx:Anchor xlink:href="http://www.opengis.net/def/crs/EPSG/0/{epsg_code}">EPSG:{epsg_code}</gmx:Anchor>
                </gmd:code>
            </gmd:RS_Identifier>
        </gmd:referenceSystemIdentifier>
    </gmd:MD_ReferenceSystem>
</gmd:referenceSystemInfo>
""" for epsg_code in epsg_codes
        ]),

        # title of data
        'title': title,

        # date of dataset
        # check GeoServer's REST API, consider revision or publication dateType
        'date': f"""
<gmd:CI_Date>
    <gmd:date>
        <gco:Date>{date}</gco:Date>
    </gmd:date>
    <gmd:dateType>
        <gmd:CI_DateTypeCode codeListValue="{date_type}" codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode">{date_type}</gmd:CI_DateTypeCode>
    </gmd:dateType>
</gmd:CI_Date>
""",

        # it must be URI, but text node is optional (MZP-CORINE)
        # it can point to Layman's Layer endpoint
        'data_identifier': f'<gmx:Anchor xlink:href="{data_identifier}">{data_identifier_label}</gmx:Anchor>',

        'abstract': '<gmd:abstract gco:nilReason="unknown" />' if abstract is None else f"""
<gmd:abstract>
    <gco:CharacterString>{abstract}</gco:CharacterString>
</gmd:abstract>
""",

        'graphic_url': url_for('rest_layer_thumbnail.get', username=username, layername=layername, _external=True),

        'extent': """
<gmd:EX_GeographicBoundingBox>
    <gmd:westBoundLongitude>
        <gco:Decimal>{}</gco:Decimal>
    </gmd:westBoundLongitude>
    <gmd:eastBoundLongitude>
        <gco:Decimal>{}</gco:Decimal>
    </gmd:eastBoundLongitude>
    <gmd:southBoundLatitude>
        <gco:Decimal>{}</gco:Decimal>
    </gmd:southBoundLatitude>
    <gmd:northBoundLatitude>
        <gco:Decimal>{}</gco:Decimal>
    </gmd:northBoundLatitude>
</gmd:EX_GeographicBoundingBox>
""".format(*extent),

        'wms_url': ows_url,

        'wfs_url': ows_url,

        'layer_endpoint': url_for('rest_layer.get', username=username, layername=layername, _external=True),


        ###############################################################################################################
        # GUESSABLE BY LAYMAN
        ###############################################################################################################

        'scale_denominator': '<gmd:denominator gco:nilReason="unknown" />' if scale_denominator is None else f"""
<gmd:denominator>
    <gco:Integer>{scale_denominator}</gco:Integer>
</gmd:denominator>
""",

        # code for no language is "zxx"
        'dataset_language': '<gmd:language gco:nilReason="unknown" />' if dataset_language is None else f"""
<gmd:language>
    <gmd:LanguageCode codeListValue=\"{dataset_language}\" codeList=\"http://www.loc.gov/standards/iso639-2/\">{dataset_language}</gmd:LanguageCode>
</gmd:language>
""",

    }

    return result

