# Publishing maps

Using REST API it is possible to publish maps (map compositions) e.g. from QGIS. Let's describe how this process can be implemented in technical way.

We will distinguish two types of QGIS maps:
- maps composed from WMS layers
- maps composed from WMS layers and local vector files

## Maps composed from WMS layers
In QGIS side, you need to implement following steps.

First, compose JSON valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema). For Layman, especially `name`, `title`, `abstract`, and `layers` attributes are important. Each layer must have `className` attribute equal to `HSLayers.Layer.WMS`.

Then save the file to Layman using [POST Maps](rest.md#post-maps) endpoint. You will need to set some sample username (Layman is not connected to any authorization service at this moment).

In the response you will obtain
 - `name` of the map unique within user's namespace
 - `url` of the map pointing to [GET Map](rest.md#get-map)
 
 Later on, you can
 - get metadata about this map using [GET Map](rest.md#get-map)
 - get uploaded JSON file using [GET Map File](rest.md#get-map-file)
 - update the map using [PUT Map](rest.md#put-map)
 - delete the map using [DELETE Map](rest.md#delete-map)
 
 Also, you can obtain list of all maps using [GET Maps](rest.md#get-maps).