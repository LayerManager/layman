from layman import settings, authz
from layman.common import empty_method
from layman.common.micka import util as common_util
from . import csw
from ..layer_class import Layer

PATCH_MODE = csw.PATCH_MODE

pre_publication_action_check = empty_method
post_layer = empty_method

get_layer_info = csw.get_layer_info
delete_layer = csw.delete_layer
get_metadata_comparison = csw.get_metadata_comparison
patch_layer = empty_method


# pylint: disable=unused-argument
def soap_insert(publication: Layer, *, access_rights, actor_name=None):
    is_public = authz.is_user_in_access_rule(settings.RIGHTS_EVERYONE_ROLE, access_rights['read'])
    template_path, prop_values = csw.get_template_path_and_values(publication, http_method='post')
    common_util.soap_insert_record_from_template(template_path, prop_values, csw.METADATA_PROPERTIES, is_public)
