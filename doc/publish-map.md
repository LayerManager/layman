# Publishing maps

Using REST API it is possible to publish maps (map compositions) e.g. from QGIS. Let's describe how this process can be implemented in a technical way.

Two types of QGIS maps are considered:
- [maps composed from WMS layers](#maps-composed-from-wms-layers)
- [maps composed from vector files](#maps-composed-from-vector-files)


## Maps composed from WMS layers
In QGIS, you need to implement following steps.

First, compose JSON valid against [map-composition schema](https://github.com/hslayers/map-compositions). For Layman, especially `describedBy`, `name`, `title`, `abstract`, `layers`, `projection`, and `extent attributes are important. Each layer must have `className` attribute equal to `HSLayers.Layer.WMS` or `WMS`.

Then save the file to Layman using [POST Workspace Maps](rest.md#post-workspace-maps) endpoint. Well-known [requests](https://requests.readthedocs.io/en/latest/) module can be used for sending HTTP requests. See especially
- [More complicated POST requests](https://requests.readthedocs.io/en/latest/user/quickstart/#more-complicated-post-requests)
- [POST a Multipart-Encoded File](https://requests.readthedocs.io/en/latest/user/quickstart/#post-a-multipart-encoded-file)
- [POST Multiple Multipart-Encoded Files](https://requests.readthedocs.io/en/latest/user/advanced/#post-multiple-multipart-encoded-files)

In response of [POST Workspace Maps](rest.md#post-workspace-maps) you will obtain
 - `name` of the map unique within all maps in used [workspace](models.md#workspace)
 - `url` of the map pointing to [GET Map](rest.md#get-map)
 
 Later on, you can
 - get metadata about this map using [GET Map](rest.md#get-map)
 - get uploaded JSON file using [GET Map File](rest.md#get-map-file)
 - update the map using [PATCH Map](rest.md#patch-map)
 - delete the map using [DELETE Map](rest.md#delete-map)
 
 Also, you can obtain list of all maps using [GET Workspace Maps](rest.md#get-workspace-maps).
 
 
 ## Maps composed from vector files
In case of maps composed from vector files, it is recommended first to publish each file as one WMS layer at Layman. Having each vector file as one WMS layer at Layman, you can then save map composition of WMS layers in the same way as in [previous example](#maps-composed-from-wms-layers).

Remember that Layman supports only CRS projections defined by [LAYMAN_INPUT_SRS_LIST](./env-settings.md#LAYMAN_INPUT_SRS_LIST) and [LAYMAN_OUTPUT_SRS_LIST](./env-settings.md#LAYMAN_OUTPUT_SRS_LIST) for publishing layers. Therefore compositions that use WMS layers provided by Layman must use one of supported projections, otherwise these layers can not be displayed.

In QGIS, you need to implement following steps.

First, publish each layer whose data source is local ShapeFile or GeoJSON as WMS layer using [POST Workspace Layers](rest.md#post-workspace-layers) endpoint. Do not forget to respect supported projection (see `crs` input parameter). Also set `style` parameter to layer style, otherwise the data file will be displayed with default GeoServer style.

In response of [POST Workspace Layers](rest.md#post-workspace-layers) you will obtain
 - `name` of the layer unique within all layers in used [workspace](models.md#workspace)
 - `url` of the layer pointing to [GET Workspace Layer](rest.md#get-workspace-layer)
 
In response of [GET Workspace Layer](rest.md#get-workspace-layer) you will obtain among others URL of WMS endpoint of the layer (`wms/url`). Together with `name` of the layer you have now enough information to represent the original local vector file as WMS layer.

Continue with the same steps as in [previous example](#maps-composed-from-wms-layers).
