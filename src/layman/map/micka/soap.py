from flask import current_app
from . import csw
from .. import MAP_TYPE
from layman.common.micka import util as common_util
from layman import settings, LaymanError, authz
from layman.map.filesystem.uuid import get_map_uuid

get_map_infos = csw.get_map_infos

get_map_info = csw.get_map_info

post_map = csw.post_map

get_publication_infos = csw.get_publication_infos

get_publication_uuid = csw.get_publication_uuid

get_metadata_comparison = csw.get_metadata_comparison

delete_map = csw.delete_map


def pre_publication_action_check(username, layername):
    pass


def patch_map(username, mapname, metadata_properties_to_refresh=None, access_rights=None, actor_name=None):
    common_util.patch_publication_by_soap(workspace=username,
                                          publ_type=MAP_TYPE,
                                          publ_name=mapname,
                                          metadata_properties_to_refresh=metadata_properties_to_refresh,
                                          actor_name=actor_name,
                                          access_rights=access_rights,
                                          csw_source=csw,
                                          csw_patch_method=csw.patch_map,
                                          soap_insert_method=soap_insert,
                                          )


def soap_insert(username, mapname, access_rights=None, actor_name=None):
    is_public = authz.is_user_in_access_rule(settings.RIGHTS_EVERYONE_ROLE, access_rights['read'])
    template_path, prop_values = csw.get_template_path_and_values(username, mapname, http_method='post', actor_name=actor_name)
    common_util.soap_insert_record_from_template(template_path, prop_values, csw.METADATA_PROPERTIES, is_public)
