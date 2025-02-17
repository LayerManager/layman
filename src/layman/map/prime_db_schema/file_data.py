from layman.common import empty_method, empty_method_returns_dict
from layman.common.prime_db_schema import publications
from .. import MAP_TYPE

get_map_info = empty_method_returns_dict
patch_map = empty_method
pre_publication_action_check = empty_method
post_map = empty_method
get_metadata_comparison = empty_method


def delete_map(workspace, layername):
    publications.set_bbox(workspace, MAP_TYPE, layername, bbox=(None, None, None, None, ), crs=None)
