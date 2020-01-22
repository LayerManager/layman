from datetime import datetime
import os
import pathlib

from flask import current_app

from layman.common.filesystem.uuid import get_publication_uuid_file
from layman.common.micka import util as common_util
from layman.layer.filesystem.uuid import get_layer_uuid
from layman.layer.geoserver.wms import get_wms_proxy
from layman.layer.geoserver.util import get_gs_proxy_base_url
from layman.layer import LAYER_TYPE
from layman import settings, patch_mode
from layman.util import url_for_external
from urllib.parse import urljoin
from xml.sax.saxutils import escape


PATCH_MODE = patch_mode.NO_DELETE


def get_metadata_uuid(uuid):
    return f"m-{uuid}" if uuid is not None else None


def get_layer_info(username, layername):
    uuid = get_layer_uuid(username, layername)
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
    template_path, template_values = get_template_path_and_values(username, layername)
    record = common_util.fill_template_as_pretty_str(template_path, template_values)
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
    template_values = _get_template_values(
        username=username,
        layername=layername,
        uuid=get_layer_uuid(username, layername),
        title=wms_layer.title,
        abstract=wms_layer.abstract or None,
        date=publ_datetime.strftime('%Y-%m-%d'),
        date_type='publication',
        data_identifier=url_for_external('rest_layer.get', username=username, layername=layername),
        data_identifier_label=layername,
        extent=wms_layer.boundingBoxWGS84,
        ows_url=urljoin(get_gs_proxy_base_url(), username + '/ows'),
        # TODO create config env variable to decide if to set organisation name or not
        organisation_name=unknown_value if settings.CSW_ORGANISATION_NAME_REQUIRED else None,
        data_organisation_name=unknown_value if settings.CSW_ORGANISATION_NAME_REQUIRED else None,
    )
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'record-template.xml')
    return template_path, template_values


def _get_template_values(
        username='browser',
        layername='layer',
        uuid='ca238200-8200-1a23-9399-42c9fca53542',
        title='CORINE - Krajinný pokryv CLC 90',
        abstract=None,
        organisation_name=None,
        data_organisation_name=None,
        date='2007-05-25',
        date_type='revision',
        data_identifier='http://www.env.cz/data/corine/1990',
        data_identifier_label='MZP-CORINE',
        extent=None,  # w, s, e, n
        ows_url="http://www.env.cz/corine/data/download.zip",
        epsg_codes=None,
        scale_denominator=None,
        dataset_language=None,
):
    epsg_codes = epsg_codes or ['3857', '4326']
    w, s, e, n = extent or [11.87, 48.12, 19.13, 51.59]
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

        # it must be URI, but text node is optional (MZP-CORINE)
        # it can point to Layman's Layer endpoint
        'data_identifier': f'<gmx:Anchor xlink:href="{data_identifier}">{escape(data_identifier_label)}</gmx:Anchor>',

        'abstract': '<gmd:abstract gco:nilReason="unknown" />' if abstract is None else f"""
<gmd:abstract>
    <gco:CharacterString>{escape(abstract)}</gco:CharacterString>
</gmd:abstract>
""",

        'graphic_url': escape(url_for_external('rest_layer_thumbnail.get', username=username, layername=layername)),

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

        'wms_url': escape(ows_url),

        'wfs_url': escape(ows_url),

        'layer_endpoint': escape(url_for_external('rest_layer.get', username=username, layername=layername)),


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

