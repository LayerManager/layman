from layman import settings, authz
from layman.common import empty_method
from layman.common.micka import util as common_util
from . import csw
from ..map_class import Map

pre_publication_action_check = empty_method

get_map_info = csw.get_map_info
post_map = csw.post_map
get_metadata_comparison = csw.get_metadata_comparison
delete_map = csw.delete_map


def patch_map(publication: Map, *, metadata_properties_to_refresh=None, access_rights=None, actor_name=None):
    common_util.patch_publication_by_soap(publication,
                                          metadata_properties_to_refresh=metadata_properties_to_refresh,
                                          actor_name=actor_name,
                                          access_rights=access_rights,
                                          csw_patch_method=csw.patch_map,
                                          soap_insert_method=soap_insert,
                                          )


def soap_insert(publication: Map, *, access_rights=None, actor_name=None):
    is_public = authz.is_user_in_access_rule(settings.RIGHTS_EVERYONE_ROLE, access_rights['read'])
    template_path, prop_values = csw.get_template_path_and_values(publication, http_method='post',
                                                                  actor_name=actor_name)
    common_util.soap_insert_record_from_template(template_path, prop_values, csw.METADATA_PROPERTIES, is_public)
