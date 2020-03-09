import re
import os
from datetime import datetime, date, timedelta
from xml.sax.saxutils import escape, quoteattr
from layman import settings, patch_mode
from layman.common.filesystem.uuid import get_publication_uuid_file
from layman.common.micka import util as common_util
from layman.map import MAP_TYPE
from layman.map.filesystem.uuid import get_map_uuid
from layman.map.filesystem.input_file import get_map_json, unquote_urls
from layman.layer.geoserver.util import get_gs_proxy_base_url
from layman.layer.geoserver.wms import get_layer_info as wms_get_layer_info
from layman.layer.micka.csw import get_layer_info as csw_get_layer_info
from layman.util import url_for_external, USERNAME_ONLY_PATTERN


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
                'identifier': muuid,
                'csw_url': settings.CSW_PROXY_URL,
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


def _map_json_to_operates_on(map_json):
    unquote_urls(map_json)
    gs_url = get_gs_proxy_base_url()
    gs_url = gs_url if gs_url.endswith('/') else f"{gs_url}/"
    gs_url_pattern = r'^' + re.escape(gs_url) + r'(' + USERNAME_ONLY_PATTERN + r')' + r'/ows.*$'
    layman_layer_names = []
    for map_layer in map_json['layers']:
        layer_url = map_layer.get('url', None)
        if not layer_url:
            continue
        # print(f"layer_url={layer_url}")
        match = re.match(gs_url_pattern, layer_url)
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
        layer_metadata = csw_get_layer_info(layer_username, layername)
        layer_wms = wms_get_layer_info(layer_username, layername)
        if not (layer_metadata and layer_wms):
            continue
        layer_muuid = layer_metadata['metadata']['identifier']
        layer_title = layer_wms['title']
        layer_csw_url = f"{csw_url}?SERVICE=CSW&VERSION=2.0.2&REQUEST=GetRecordById&OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&ID={layer_muuid}#_{layer_muuid}"
        operates_on.append({
            'xlink:title': layer_title,
            'xlink:href': layer_csw_url,
        })
    return operates_on


def get_template_path_and_values(username, mapname):
    uuid_file_path = get_publication_uuid_file(MAP_TYPE, username, mapname)
    publ_datetime = datetime.fromtimestamp(os.path.getmtime(uuid_file_path))
    map_json = get_map_json(username, mapname)
    operates_on = _map_json_to_operates_on(map_json)

    unknown_value = 'neznámá hodnota'
    template_values = _get_template_values(
        username=username,
        mapname=mapname,
        uuid=get_map_uuid(username, mapname),
        title=map_json['title'],
        abstract=map_json['abstract'] or None,
        publication_date=publ_datetime.strftime('%Y-%m-%d'),
        md_date_stamp=date.today().strftime('%Y-%m-%d'),
        identifier=url_for_external('rest_map.get', username=username, mapname=mapname),
        data_identifier_label=mapname,
        extent=[float(c) for c in map_json['extent']],
        # TODO create config env variable to decide if to set organisation name or not
        md_organisation_name=unknown_value if settings.CSW_ORGANISATION_NAME_REQUIRED else None,
        organisation_name=unknown_value if settings.CSW_ORGANISATION_NAME_REQUIRED else None,
        operates_on=operates_on,
    )
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'record-template.xml')
    return template_path, template_values


def _get_template_values(
        username='browser',
        mapname='map',
        uuid='af238200-8200-1a23-9399-42c9fca53543',
        title='Administrativní členění Libereckého kraje',
        abstract=None,
        md_organisation_name=None,
        organisation_name=None,
        publication_date='2007-05-25',
        md_date_stamp='2007-05-25',
        identifier='http://www.env.cz/data/liberec/admin-cleneni',
        data_identifier_label='Liberec-AdminUnits',
        extent=None,  # w, s, e, n
        epsg_codes=None,
        language=None,
        operates_on=None,
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
        ###############################################################################################################
        # KNOWN TO LAYMAN
        ###############################################################################################################

        # layer UUID with prefix "m-"
        'md_file_identifier': get_metadata_uuid(uuid),

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
        'publication_date': f"""
<gmd:CI_Date>
    <gmd:date>
        <gco:Date>{publication_date}</gco:Date>
    </gmd:date>
    <gmd:dateType>
        <gmd:CI_DateTypeCode codeListValue="publication" codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode">publication</gmd:CI_DateTypeCode>
    </gmd:dateType>
</gmd:CI_Date>
""",

        # date stamp of metadata
        'md_date_stamp': md_date_stamp,

        # it must be URI, but text node is optional (MZP-CORINE)
        # it can point to Layman's Layer endpoint
        'identifier': f'<gmx:Anchor xlink:href="{identifier}">{escape(data_identifier_label)}</gmx:Anchor>',

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

        'operates_on': '\n'.join([
            f"""
<srv:operatesOn xlink:type="simple" {
    ' '.join([f"{attr}={quoteattr(value)}" for attr, value in item.items()])
}/>
""" for item in operates_on
        ]),

        ###############################################################################################################
        # GUESSABLE BY LAYMAN
        ###############################################################################################################

        # code for no language is "zxx"
        'language': '<gmd:language gco:nilReason="unknown" />' if language is None else f"""
<gmd:language>
    <gmd:LanguageCode codeListValue=\"{language}\" codeList=\"http://www.loc.gov/standards/iso639-2/\">{language}</gmd:LanguageCode>
</gmd:language>
""",

        ###############################################################################################################
        # UNKNOWN TO LAYMAN
        ###############################################################################################################
        'md_organisation_name': '<gmd:organisationName gco:nilReason="unknown" />' if md_organisation_name is None else f"""
    <gmd:organisationName>
        <gco:CharacterString>{escape(md_organisation_name)}</gco:CharacterString>
    </gmd:organisationName>
    """,

        'organisation_name': '<gmd:organisationName gco:nilReason="unknown" />' if organisation_name is None else f"""
    <gmd:organisationName>
        <gco:CharacterString>{escape(organisation_name)}</gco:CharacterString>
    </gmd:organisationName>
    """,
    }

    return result

