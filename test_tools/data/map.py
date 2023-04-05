import json
import os
from pathlib import Path
import crs as crs_def
from layman import util as layman_util, app
from layman.common import bbox
from layman.layer.geoserver import util as layer_gs_util, wms as geoserver_wms
from .. import process_client


def get_map_with_internal_layers_json(layers, *, native_extent=None, native_crs=None):
    if not native_extent:
        with app.app_context():
            extents = [layman_util.get_publication_info(workspace, process_client.LAYER_TYPE, layer, context={'keys': ['bounding_box']})['bounding_box']
                       for workspace, layer in layers]
        native_extent = (min(minx for minx, _, _, _ in extents), min(miny for _, miny, _, _ in extents),
                         max(maxx for _, _, maxx, _ in extents), max(maxy for _, _, _, maxy in extents),)
        native_crs = crs_def.EPSG_3857
    assert native_crs

    with app.app_context():
        extent_4326 = bbox.transform(native_extent, crs_from=native_crs, crs_to=crs_def.EPSG_4326, )
    map_json = {
        "describedBy": "https://raw.githubusercontent.com/hslayers/map-compositions/2.0.0/schema.json",
        "schema_version": "2.0.0",
        "abstract": "Map generated for internal layers",
        "title": "Map of internal layers",
        "extent": extent_4326,
        "nativeExtent": native_extent,
        "projection": native_crs,
        "layers": [
            {
                "metadata": {},
                "visibility": True,
                "opacity": 1,
                "title": "Defini\u010dn\u00ed body administrativn\u00edch celk\u016f",
                "className": "HSLayers.Layer.WMS",
                "singleTile": True,
                "wmsMaxScale": 0,
                "legends": [
                    "https%3A%2F%2Fgeoportal.kraj-lbc.cz%2Fcgi-bin%2Fmapserv%3Fmap%3D%2Fdata%2Fgis%2FMapServer%2Fprojects%2Fwms%2Fatlas%2Fadministrativni_cleneni.map%26version%3D1.3.0%26service%3DWMS%26request%3DGetLegendGraphic%26sld_version%3D1.1.0%26layer%3Ddefinicni_body_administrativnich_celku%26format%3Dimage%2Fpng%26STYLE%3Ddefault"
                ],
                "maxResolution": None,
                "minResolution": 0,
                "url": "https%3A%2F%2Fgeoportal.kraj-lbc.cz%2Fcgi-bin%2Fmapserv%3Fmap%3D%2Fdata%2Fgis%2FMapServer%2Fprojects%2Fwms%2Fatlas%2Fadministrativni_cleneni.map%26",
                "params": {
                    "LAYERS": "definicni_body_administrativnich_celku",
                    "INFO_FORMAT": "application/vnd.ogc.gml",
                    "FORMAT": "image/png",
                    "FROMCRS": "EPSG:3857",
                    "VERSION": "1.3.0"
                },
                "dimensions": {}
            }
        ]
    }
    gs_url = layer_gs_util.get_gs_proxy_base_url()
    gs_url = gs_url if gs_url.endswith('/') else f"{gs_url}/"
    for workspace, layer in layers:
        geoserver_workspace = geoserver_wms.get_geoserver_workspace(workspace)
        map_json['layers'].append({
            "metadata": {},
            "visibility": True,
            "opacity": 1,
            "title": layer,
            "className": "HSLayers.Layer.WMS",
            "singleTile": True,
            "url": f"{gs_url}{geoserver_workspace}/ows",
            "params": {
                "LAYERS": layer,
                "FORMAT": "image/png"
            }
        })
    return map_json


def create_map_with_internal_layers_file(layers, *, file_path, native_extent=None, native_crs=None):
    map_json = get_map_with_internal_layers_json(layers, native_extent=native_extent, native_crs=native_crs)
    file_dir = os.path.dirname(file_path)
    Path(file_dir).mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding="utf-8") as out:
        out.write(json.dumps(map_json, indent=2))
