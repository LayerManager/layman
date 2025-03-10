from layman.common import empty_method, empty_method_returns_dict
from layman.common.prime_db_schema import publications
from ..map_class import Map

get_map_info = empty_method_returns_dict
patch_map = empty_method
pre_publication_action_check = empty_method
post_map = empty_method
get_metadata_comparison = empty_method


def delete_map(map: Map):
    publications.set_bbox(map.workspace, map.type, map.name, bbox=(None, None, None, None, ), crs=None)
