# Publishing maps

Using REST API it is possible to publish maps (map compositions) e.g. from QGIS. Let's describe how this process can be implemented in technical way.

Two types of QGIS maps are considered:
- [maps composed from WMS layers](#maps-composed-from-wms-layers)
- [maps composed from vector files](#maps-composed-from-vector-files)


## Maps composed from WMS layers
In QGIS, you need to implement following steps.

First, compose JSON valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema). For Layman, especially `name`, `title`, `abstract`, and `layers` attributes are important. Each layer must have `className` attribute equal to `HSLayers.Layer.WMS`.

Then save the file to Layman using [POST Maps](rest.md#post-maps) endpoint. You need to set any sample username as Layman is not connected to any authorization service at this moment. Well-known [requests](http://docs.python-requests.org/en/latest/) module can be used for sending HTTP requests. See especially
- [More complicated POST requests](http://docs.python-requests.org/en/latest/user/quickstart/#more-complicated-post-requests)
- [POST a Multipart-Encoded File](http://docs.python-requests.org/en/latest/user/quickstart/#post-a-multipart-encoded-file)
- [POST Multiple Multipart-Encoded Files](http://docs.python-requests.org/en/latest/user/advanced/#post-multiple-multipart-encoded-files)

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

Remember that Layman currently supports only `EPSG:4326` and `EPSG:3857` projections for publishing WMS layers. So compositions that uses WMS layers provided by Layman must use one of the two projections, otherwise these layers can not be displayed. 

In QGIS, you need to implement following steps.

First, publish each layer whose data source is local ShapeFile or GeoJSON as WMS layer using [POST Layers](rest.md#post-layers) endpoint. Input data file must be in `EPSG:4326` or `EPSG:3857` projection (see `crs` input parameter), because other data projections are currently not supported by Layman. Also set `sld` parameter to layer style, otherwise the data file will be displayed with default GeoServer style.

In response of [POST Layers](rest.md#post-layers) you will obtain
 - `name` of the layer unique within user's layers
 - `url` of the layer pointing to [GET Layer](rest.md#get-layer)
 
In response of [GET Layer](rest.md#get-layer) you will obtain among others URL of WMS endpoint of the layer (`wms/url`). Together with `name` of the layer you have now enough information to represent the original local vector file as WMS layer.

Continue with the same steps as in [previous example](#maps-composed-from-wms-layers).