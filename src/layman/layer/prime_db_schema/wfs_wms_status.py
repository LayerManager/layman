from db import util as db_util
from layman import patch_mode, settings
from layman.common import empty_method, empty_method_returns_dict
from .. import LAYER_TYPE


DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

get_layer_info = empty_method_returns_dict
pre_publication_action_check = empty_method
get_metadata_comparison = empty_method_returns_dict
patch_layer = empty_method
post_layer = empty_method
delete_layer = empty_method


def set_after_restart():
    query = f'''update {DB_SCHEMA}.publications set
    wfs_wms_status = %s
    where type = %s
      and wfs_wms_status = %s;'''
    params = (settings.EnumWfsWmsStatus.NOT_AVAILABLE.value, LAYER_TYPE, settings.EnumWfsWmsStatus.PREPARING.value,)
    db_util.run_statement(query, params)
