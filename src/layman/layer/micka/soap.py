from flask import current_app
from requests.exceptions import HTTPError, ConnectionError
import traceback
from . import csw
from layman import settings, LaymanError
from layman.common.micka import util as common_util

PATCH_MODE = csw.PATCH_MODE

get_layer_info = csw.get_layer_info

get_layer_infos = csw.get_layer_infos

update_layer = csw.update_layer

get_publication_infos = csw.get_publication_infos

get_publication_uuid = csw.get_publication_uuid

delete_layer = csw.delete_layer

get_metadata_comparison = csw.get_metadata_comparison


def soap_insert(username, layername):
    template_path, prop_values = csw.get_template_path_and_values(username, layername, http_method='post')
    record = common_util.fill_xml_template_as_pretty_str(template_path, prop_values, csw.METADATA_PROPERTIES)
    try:
        muuid = common_util.soap_insert({
            'record': record,
            'edit_user': settings.CSW_BASIC_AUTHN[0],
            'read_user': settings.CSW_BASIC_AUTHN[0],
        })
    except (HTTPError, ConnectionError):
        current_app.logger.info(traceback.format_exc())
        raise LaymanError(38)
    return muuid
