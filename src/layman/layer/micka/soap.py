from layman import settings, authz
from layman.common import empty_method
from layman.common.micka import util as common_util
from . import csw
from .. import LAYER_TYPE

PATCH_MODE = csw.PATCH_MODE

pre_publication_action_check = empty_method
post_layer = empty_method

get_layer_info = csw.get_layer_info
get_publication_uuid = csw.get_publication_uuid
delete_layer = csw.delete_layer
get_metadata_comparison = csw.get_metadata_comparison


def patch_layer(workspace, layername, metadata_properties_to_refresh, access_rights=None):
    common_util.patch_publication_by_soap(workspace=workspace,
                                          publ_type=LAYER_TYPE,
                                          publ_name=layername,
                                          metadata_properties_to_refresh=metadata_properties_to_refresh,
                                          actor_name=None,
                                          access_rights=access_rights,
                                          csw_patch_method=csw.patch_layer,
                                          soap_insert_method=soap_insert,
                                          )


def soap_insert(username, layername, access_rights, _actor_name=None):
    is_public = authz.is_user_in_access_rule(settings.RIGHTS_EVERYONE_ROLE, access_rights['read'])
    template_path, prop_values = csw.get_template_path_and_values(username, layername, http_method='post')
    common_util.soap_insert_record_from_template(template_path, prop_values, csw.METADATA_PROPERTIES, is_public)
