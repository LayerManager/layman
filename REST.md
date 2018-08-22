# REST API

## Overview
|Endpoint|URL|GET|POST|PUT|DELETE|
|---|---|---|---|---|---|
|Layers|`/rest/<user>/layers`|[GET](#get-layers)| [POST](#post-layers) | x | x |
|Layer|`/rest/<user>/layers/<layername>`|[GET](#get-layer)| x | [PUT](#put-layer) | [DELETE](#delete-layer) |
|Layer Thumbnail|`/rest/<user>/layers/<layername>/thumbnail`|[GET](#get-layer-thumbnail)| x | x | x |

#### Path parameters
- **user**, `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`
   - owner of the layer
   - it can be almost any string matching the regular expression (some keywords are not allowed)
   - it is not real user of file system, DB, or GeoServer

## Layers
### URL
`/rest/<user>/layers`

### GET Layers
Get list of layers available at WMS and WFS endpoints.

#### Input parameters
None.
#### Output
JSON array of objects representing available layers with following structure:
- **name**: String. Name of the layer.
- **url**: String. URL of the layer. It points to [GET Layer](#get-layer).

### POST Layers
Publish vector data file as new layer of WMS and WFS.

Processing chain consists of few steps:
- save file to user's directory within GeoServer data directory
- import the file to PostgreSQL database as new table into user's schema, including geometry transformation to EPSG:3857
- publish the table as new layer (feature type) within user's workspace of GeoServer
- generate thumbnail image

If user's directory, database schema, GeoServer's worskpace, or GeoServer's store does not exist yet, it is created on demand.

#### Input parameters
- **file**, file
   - GeoJSON file
- *name*, string
   - computer-friendly identifier of the layer
   - must be unique within one user
   - by default, it is file name without extension
   - will be automatically adjusted using `to_safe_layer_name` function
- *title*, string `.+`
   - human readable name of the layer
   - by default it is layer_name
- *description*
   - by default it is empty string
- *crs*, string `EPSG:3857` or `EPSG:4326`
   - CRS of the file
   - by default it is read/guessed from input file
- *sld*, SLD file
   - by default default SLD style of GeoServer is used

#### Output
JSON array of objects representing posted layers with following structure:
- **name**: String. Name of the layer.
- **url**: String. URL of the layer. It points to [GET Layer](#get-layer).

## Layer
### URL
`/rest/<user>/layers/<layername>`

#### Path parameters
- **layername**
   - layer name used for identification
   - it can be obtained from responses of [GET Layers](#get-layers), [POST Layers](#post-layers), and all responses of this endpoint

### GET Layer
Get information about existing layer.

#### Input parameters
None.
#### Output
JSON object with following structure:
- **name**: String. Layer name within user's workspace of GeoServer. It should be used for identifying layer within WMS and WFS endpoints.
- **url**: String. URL pointing to this endpoint.
- **title**: String.
- **description**: String.
- **wms**
  - *url*: String. URL of WMS endpoint. It points to WMS endpoint of user's workspace.
  - *status*: Status information about GeoServer import and availability of WMS layer. No status object = import was successfully completed and WMS layer is available.
- **wfs**
  - *url*: String. URL of WFS endpoint. It points to WFS endpoint of user's workspace.
  - *status*: Status information about GeoServer import and availability of WFS feature type. No status object = import was successfully completed and the feature type is available.
- **thumbnail**
  - *url*: String. URL of layer thumbnail. It points to [GET Layer Thumbnail](#get-layer-thumbnail).
  - *status*: Status information about generating and availability of thumbnail. No status object = thumbnail was successfully generated and it is available.
- **file**
  - *name*: String. Path to input vector data file that was imported to the DB table. Path is relative to user's directory.
  - *status*: Status information about saving and availability of files. No status object = file was successfully saved.
- **db_table**
  - **name**: String. DB table name within PostgreSQL user's schema. This table is used as GeoServer source of layer.
  - *status*: Status information about DB import and availability of the table. No status object = import was successfully completed.


### PUT Layer
Update information about existing layer.

#### Input parameters
Parameters have same meaning as in case of [POST Layers](#post-layers).
- *file*, file
   - If provided, current layer vector data file will be deleted and replaced by this file. GeoServer layer, DB table, and thumbnail will be temporarily deleted and created again using the new file.
- *title*
- *description*
- *crs*, string `EPSG:3857` or `EPSG:4326`
   - Taken into account only if `file` is provided.
- *sld*, SLD file
   - If provided, current layer thumbnail will be temporarily deleted and created again using the new style.

#### Output
JSON object, same as in case of [GET](#get-layer).


### DELETE Layer
Delete existing layer and all associated sources, including vector data file and DB table.

#### Input parameters
None.

#### Output
JSON object representing deleted layer:
- **name**: String. Former Name of the layer.
- **url**: String. Former URL of the layer. It points to [GET Layer](#get-layer).


## Layer Thumbnail
### URL
`/rest/<user>/layers/<layername>/thumbnail`
### GET Layer Thumbnail
Get thumbnail of the layer in PNG format, 300x300 px, transparent background.

#### Input parameters
None.
#### Output
PNG image.
