import re
from urllib.parse import urlparse, unquote

from requests.structures import CaseInsensitiveDict


def find_maps_containing_layer(layer_workspace, layer_name):
    from layman.layer import LAYER_TYPE
    from layman.layer.geoserver import util as layer_gs_util
    from layman.map.filesystem import input_file as map_input_file
    from layman.map.util import find_maps_by_grep
    from layman.util import get_publication_info

    gs_url = layer_gs_util.get_gs_proxy_base_url()
    gs_url = gs_url if gs_url.endswith('/') else f"{gs_url}/"
    gs_domain = urlparse(gs_url).hostname

    layer_info = get_publication_info(layer_workspace, LAYER_TYPE, layer_name, context={'keys': ['wms']})
    layer_wms_workspace = layer_info.get('_wms', {}).get('workspace')

    # first rough filters
    url_pattern = fr'^\s*.?url.?:\s*.*{gs_domain}.*/geoserver(/({layer_workspace}|{layer_wms_workspace}))?/(ows|wms|wfs).*,\s*$'
    url_maps = find_maps_by_grep(url_pattern)
    layer_pattern = fr'^\s*.?(layers|LAYERS).?:\s*.*{layer_name}.*\s*$'
    layer_maps = find_maps_by_grep(layer_pattern)
    maps = url_maps.intersection(layer_maps)

    # verify layer for map
    gs_ows_url_pattern = fr'^{re.escape(gs_url)}(({layer_workspace}|{layer_wms_workspace})/)?(?:ows|wms|wfs).*$'
    result_maps = set()
    for workspace, map in maps:
        map_json_raw = map_input_file.get_map_json(workspace, map)
        map_json = map_input_file.unquote_urls(map_json_raw)

        for map_layer in map_json['layers']:
            layer_url = map_layer.get('url')
            if not layer_url:
                continue
            match = re.match(gs_ows_url_pattern, layer_url)
            if not match:
                continue
            map_layers = CaseInsensitiveDict(**map_layer.get('params', {})).get('layers')
            layers = unquote(map_layers).split(',')
            if layer_name in layers or f'{layer_workspace}:{layer_name}' in layers or f'{layer_wms_workspace}:{layer_name}' in layers:
                result_maps.add((workspace, map))

    return result_maps


def update_related_publications_after_change(workspace, publication_type, publication):
    from layman.layer import LAYER_TYPE
    from layman.map import MAP_TYPE
    from layman.util import patch_after_feature_change

    if publication_type == LAYER_TYPE:
        maps = find_maps_containing_layer(workspace, publication)
        for map_workspace, map_name in maps:
            patch_after_feature_change(map_workspace, MAP_TYPE, map_name)
