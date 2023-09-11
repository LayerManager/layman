def update_related_publications_after_change(workspace, publication_type, publication):
    from layman.layer import LAYER_TYPE
    from layman.map import MAP_TYPE
    from layman.util import patch_after_feature_change, get_publication_info

    if publication_type == LAYER_TYPE:
        maps = get_publication_info(workspace, publication_type, publication, context={'keys': ['layer_maps']})['_layer_maps']
        for map_obj in maps:
            patch_after_feature_change(map_obj['workspace'], MAP_TYPE, map_obj['name'])
