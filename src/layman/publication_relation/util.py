def update_related_publications_after_change(workspace, publication_type, publication):
    from layman.layer import LAYER_TYPE
    from layman.map import MAP_TYPE
    from layman.util import patch_after_feature_change, get_publication_info

    if publication_type == LAYER_TYPE:
        maps = get_publication_info(workspace, publication_type, publication, context={'keys': ['used_in_maps']})['used_in_maps']
        for map_obj in maps:
            patch_after_feature_change(map_obj['workspace'], MAP_TYPE, map_obj['name'])


def check_no_internal_workspace_name_layer(map_json, *, x_forwarded_items):
    from layman import names, LaymanError
    from layman.map.util import get_internal_gs_layers_from_json
    from layman.layer.prime_db_schema.table import get_layer_info
    found_gs_layer = get_internal_gs_layers_from_json(map_json, x_forwarded_items=x_forwarded_items)
    found_layers = []
    for layer_idx, gs_workspace, gs_layer in found_gs_layer:
        layer_uuid = names.geoserver_layername_to_uuid(geoserver_workspace=gs_workspace,
                                                       geoserver_name=gs_layer)
        if not layer_uuid:
            workspace = gs_workspace[:-4] if gs_workspace.endswith('_wms') else gs_workspace
            layer = get_layer_info(workspace=workspace, layername=gs_layer)
            if layer:
                found_layers.append({
                    'layer_index': layer_idx,
                    'workspace': gs_workspace,
                    'layer_name': gs_layer,
                }
                )
    if found_layers:
        raise LaymanError(59, {
            'wrongly_referenced_layers': found_layers,
        })
