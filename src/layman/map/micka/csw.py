import os
from datetime import datetime, date, timedelta
from xml.sax.saxutils import escape
from layman import settings, patch_mode
from layman.common.filesystem.uuid import get_publication_uuid_file
from layman.common.micka import util as common_util
from layman.map import MAP_TYPE
from layman.map.filesystem.uuid import get_map_uuid
from layman.map.filesystem.input_file import get_map_json
from layman.util import url_for_external


PATCH_MODE = patch_mode.NO_DELETE


def get_metadata_uuid(uuid):
    return f"m-{uuid}" if uuid is not None else None


def get_map_info(username, mapname):
    uuid = get_map_uuid(username, mapname)
    csw = common_util.create_csw()
    if uuid is None or csw is None:
        return {}
    muuid = get_metadata_uuid(uuid)
    csw.getrecordbyid(id=[muuid], esn='brief')
    if muuid in csw.records:
        return {
            'metadata': {
                'csw_url': settings.CSW_URL,
                'record_url': settings.CSW_RECORD_URL.format(identifier=muuid),
            }
        }
    else:
        return {}


def get_map_names(username):
    # TODO consider reading map names from all Micka's metadata records by linkage URL
    return []


def get_publication_names(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    return []


def get_publication_uuid(username, publication_type, publication_name):
    return None


def delete_map(username, mapname):
    uuid = get_map_uuid(username, mapname)
    muuid = get_metadata_uuid(uuid)
    if muuid is None:
        return
    common_util.csw_delete(muuid)


def post_map(username, mapname):
    pass


def patch_map(username, mapname):
    pass


def csw_insert(username, mapname):
    template_path, template_values = get_template_path_and_values(username, mapname)
    record = common_util.fill_template_as_pretty_str(template_path, template_values)
    muuid = common_util.csw_insert({
        'record': record
    })
    return muuid


def get_template_path_and_values(username, mapname):
    uuid_file_path = get_publication_uuid_file(MAP_TYPE, username, mapname)
    publ_datetime = datetime.fromtimestamp(os.path.getmtime(uuid_file_path))
    map_json = get_map_json(username, mapname)

    unknown_value = 'neznámá hodnota'
    template_values = _get_template_values(
        username=username,
        mapname=mapname,
        uuid=get_map_uuid(username, mapname),
        title=map_json['title'],
        abstract=map_json['abstract'] or None,
        date=publ_datetime.strftime('%Y-%m-%d'),
        date_type='publication',
        date_stamp=date.today().strftime('%Y-%m-%d'),
        data_identifier=url_for_external('rest_map.get', username=username, mapname=mapname),
        data_identifier_label=mapname,
        extent=[float(c) for c in map_json['extent']],
        # TODO create config env variable to decide if to set organisation name or not
        organisation_name=unknown_value if settings.CSW_ORGANISATION_NAME_REQUIRED else None,
        data_organisation_name=unknown_value if settings.CSW_ORGANISATION_NAME_REQUIRED else None,
    )
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'record-template.xml')
    return template_path, template_values


def _get_template_values(
        username='browser',
        mapname='map',
        uuid='af238200-8200-1a23-9399-42c9fca53543',
        title='Administrativní členění Libereckého kraje',
        abstract=None,
        organisation_name=None,
        data_organisation_name=None,
        date='2007-05-25',
        date_type='revision',
        date_stamp='2007-05-25',
        data_identifier='http://www.env.cz/data/liberec/admin-cleneni',
        data_identifier_label='Liberec-AdminUnits',
        extent=None,  # w, s, e, n
        epsg_codes=None,
        dataset_language=None,
):
    epsg_codes = epsg_codes or ['3857']
    w, s, e, n = extent or [14.62, 50.58, 15.42, 50.82]
    extent = [max(w, -180), max(s, -90), min(e, 180), min(n, 90)]

    result = {
        ###############################################################################################################
        # KNOWN TO LAYMAN
        ###############################################################################################################

        # layer UUID with prefix "m-"
        'file_identifier': get_metadata_uuid(uuid),

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

        # date stamp of metadata
        'date_stamp': f"""<gco:Date>{date_stamp}</gco:Date>""",

        # it must be URI, but text node is optional (MZP-CORINE)
        # it can point to Layman's Layer endpoint
        'data_identifier': f'<gmx:Anchor xlink:href="{data_identifier}">{escape(data_identifier_label)}</gmx:Anchor>',

        'abstract': '<gmd:abstract gco:nilReason="unknown" />' if abstract is None else f"""
<gmd:abstract>
    <gco:CharacterString>{escape(abstract)}</gco:CharacterString>
</gmd:abstract>
""",

        'graphic_url': escape(url_for_external('rest_map_thumbnail.get', username=username, mapname=mapname)),

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
""".format(extent[0], extent[2], extent[1], extent[3]),

        'map_endpoint': escape(url_for_external('rest_map.get', username=username, mapname=mapname)),

        'map_file_endpoint': escape(url_for_external('rest_map_file.get', username=username, mapname=mapname)),


        ###############################################################################################################
        # GUESSABLE BY LAYMAN
        ###############################################################################################################

        # code for no language is "zxx"
        'dataset_language': '<gmd:language gco:nilReason="unknown" />' if dataset_language is None else f"""
<gmd:language>
    <gmd:LanguageCode codeListValue=\"{dataset_language}\" codeList=\"http://www.loc.gov/standards/iso639-2/\">{dataset_language}</gmd:LanguageCode>
</gmd:language>
""",

        ###############################################################################################################
        # UNKNOWN TO LAYMAN
        ###############################################################################################################
        'organisation_name': '<gmd:organisationName gco:nilReason="unknown" />' if organisation_name is None else f"""
    <gmd:organisationName>
        <gco:CharacterString>{escape(organisation_name)}</gco:CharacterString>
    </gmd:organisationName>
    """,

        'data_organisation_name': '<gmd:organisationName gco:nilReason="unknown" />' if data_organisation_name is None else f"""
    <gmd:organisationName>
        <gco:CharacterString>{escape(data_organisation_name)}</gco:CharacterString>
    </gmd:organisationName>
    """,
    }

    return result

