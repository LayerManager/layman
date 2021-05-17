from layman import util as layman_util, app
from layman.common import bbox
from layman.layer.geoserver import util as layer_gs_util
from .. import process_client


def get_map_with_internal_layers_json(layers, *, extent_3857=None):
    if not extent_3857:
        with app.app_context():
            extents = [layman_util.get_publication_info(workspace, process_client.LAYER_TYPE, layer, context={'keys': ['wms', 'bounding_box']})['bounding_box']
                       for workspace, layer in layers]
        extent_3857 = (min([minx for minx, _, _, _ in extents]), min([miny for _, miny, _, _ in extents]),
                       max([maxx for _, _, maxx, _ in extents]), min([maxy for _, _, _, maxy in extents]), )

    with app.app_context():
        extent_4326 = bbox.transform(extent_3857, 3857, 4326)
    map_json = f'''
{{
    "abstract": "Map generated for internal layers",
    "title": "Map of internal layers",
    "extent": [
        "{extent_4326[0]}",
        "{extent_4326[1]}",
        "{extent_4326[2]}",
        "{extent_4326[3]}"
    ],
    "projection": "epsg:3857",
    "layers": [
        {{
            "metadata": {{}},
            "visibility": true,
            "opacity": 1,
            "title": "Defini\u010dn\u00ed body administrativn\u00edch celk\u016f",
            "className": "HSLayers.Layer.WMS",
            "singleTile": true,
            "wmsMaxScale": 0,
            "legends": [
                "https%3A%2F%2Fgeoportal.kraj-lbc.cz%2Fcgi-bin%2Fmapserv%3Fmap%3D%2Fdata%2Fgis%2FMapServer%2Fprojects%2Fwms%2Fatlas%2Fadministrativni_cleneni.map%26version%3D1.3.0%26service%3DWMS%26request%3DGetLegendGraphic%26sld_version%3D1.1.0%26layer%3Ddefinicni_body_administrativnich_celku%26format%3Dimage%2Fpng%26STYLE%3Ddefault"
            ],
            "maxResolution": null,
            "minResolution": 0,
            "url": "https%3A%2F%2Fgeoportal.kraj-lbc.cz%2Fcgi-bin%2Fmapserv%3Fmap%3D%2Fdata%2Fgis%2FMapServer%2Fprojects%2Fwms%2Fatlas%2Fadministrativni_cleneni.map%26",
            "params": {{
                "LAYERS": "definicni_body_administrativnich_celku",
                "INFO_FORMAT": "application/vnd.ogc.gml",
                "FORMAT": "image/png",
                "FROMCRS": "EPSG:3857",
                "VERSION": "1.3.0"
            }},
            "dimensions": {{}}
        }}
'''
    gs_url = layer_gs_util.get_gs_proxy_base_url()
    gs_url = gs_url if gs_url.endswith('/') else f"{gs_url}/"
    for workspace, layer in layers:
        map_json = map_json + f''',
        {{
            "metadata": {{}},
            "visibility": true,
            "opacity": 1,
            "title": "{layer}",
            "className": "HSLayers.Layer.WMS",
            "singleTile": true,
            "url": "{gs_url}{workspace}/ows",
            "params": {{
                "LAYERS": "{layer}",
                "FORMAT": "image/png"
            }}
        }}'''
    map_json = map_json + '''
    ]
}'''
    return map_json


def create_map_with_internal_layers_file(layers, *, extent_3857=None):
    file_path = f'tmp/map_with_internal_layers.json'
    map_json = get_map_with_internal_layers_json(layers, extent_3857=extent_3857)
    with open(file_path, 'w') as out:
        out.write(map_json)
    return file_path
