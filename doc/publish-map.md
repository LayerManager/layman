# Publishing maps

Using REST API it is possible to publish maps (map compositions) e.g. from QGIS. Let's describe how this process can be implemented in a technical way.

Two types of QGIS maps are considered:
- [maps composed from WMS layers](#maps-composed-from-wms-layers)
- [maps composed from vector files](#maps-composed-from-vector-files)


## Maps composed from WMS layers
In QGIS, you need to implement following steps.

First, compose JSON valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema). For Layman, especially `name`, `title`, `abstract`, and `layers` attributes are important. Each layer must have `className` attribute equal to `HSLayers.Layer.WMS`.

Then save the file to Layman using [POST Maps](rest.md#post-maps) endpoint. Well-known [requests](https://requests.readthedocs.io/en/master/) module can be used for sending HTTP requests. See especially
- [More complicated POST requests](https://requests.readthedocs.io/en/master/user/quickstart/#more-complicated-post-requests)
- [POST a Multipart-Encoded File](https://requests.readthedocs.io/en/master/user/quickstart/#post-a-multipart-encoded-file)
- [POST Multiple Multipart-Encoded Files](https://requests.readthedocs.io/en/master/user/advanced/#post-multiple-multipart-encoded-files)

In response of [POST Maps](rest.md#post-maps) you will obtain
 - `name` of the map unique within user's maps
 - `url` of the map pointing to [GET Map](rest.md#get-map)
 
 Later on, you can
 - get metadata about this map using [GET Map](rest.md#get-map)
 - get uploaded JSON file using [GET Map File](rest.md#get-map-file)
 - update the map using [PATCH Map](rest.md#patch-map)
 - delete the map using [DELETE Map](rest.md#delete-map)
 
 Also, you can obtain list of all maps using [GET Maps](rest.md#get-maps).
 
 
 ## Maps composed from vector files
In case of maps composed from vector files, it is recommended first to publish each file as one WMS layer at Layman. Having each vector file as one WMS layer at Layman, you can then save map composition of WMS layers in the same way as in [previous example](#maps-composed-from-wms-layers).

Remember that Layman supports only `EPSG:4326` and `EPSG:3857` projections by default for publishing layers. Therefore compositions that use WMS layers provided by Layman must use one of supported projections, otherwise these layers can not be displayed.

In QGIS, you need to implement following steps.

First, publish each layer whose data source is local ShapeFile or GeoJSON as WMS layer using [POST Layers](rest.md#post-layers) endpoint. Do not forget to respect supported projection (see `crs` input parameter). Also set `sld` parameter to layer style, otherwise the data file will be displayed with default GeoServer style.

In response of [POST Layers](rest.md#post-layers) you will obtain
 - `name` of the layer unique within user's layers
 - `url` of the layer pointing to [GET Layer](rest.md#get-layer)
 
In response of [GET Layer](rest.md#get-layer) you will obtain among others URL of WMS endpoint of the layer (`wms/url`). Together with `name` of the layer you have now enough information to represent the original local vector file as WMS layer.

Continue with the same steps as in [previous example](#maps-composed-from-wms-layers).