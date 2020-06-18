from flask import current_app
from requests.exceptions import HTTPError, ConnectionError
import traceback
from . import csw
from layman.common.micka import util as common_util
from layman import settings, LaymanError


get_map_names = csw.get_map_names


get_map_info = csw.get_map_info


post_map = csw.post_map


get_publication_names = csw.get_publication_names


get_publication_uuid = csw.get_publication_uuid


get_metadata_comparison = csw.get_metadata_comparison


patch_map = csw.patch_map


delete_map = csw.delete_map


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


