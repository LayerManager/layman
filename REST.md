# REST API

## Layers
### URL
`/<user>/layers`
### POST Layers
Publish vector data file as new layer of WMS and WFS.

Processing chain consists of few steps:
- save file to user's directory within GeoServer data directory
- import the file to PostgreSQL database as new table into user's schema
- publish the table as new layer (feature type) within user's workspace of GeoServer
- generate thumbnail image

If user's directory, database schema, GeoServer's worskpace, or GeoServer's store does not exist yet, it is created on demand.

#### Input parameters
- **user**, string `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`
   - path parameter
   - owner of the file
   - it is not real user of file system, DB, or GeoServer
   - it can be any string matching the regular expression
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
   - by default it is read/guessed from input file
- *sld*, SLD file
   - by default default SLD style of GeoServer is used

#### Output
JSON object with following structure:
- **name**: String. Name of the layer.
- **url**: String. URL of the layer. It points to [GET Layer](#get-layer).

### GET Layers
Get list of layers available at WMS and WFS endpoints.

#### Input parameters
None.
#### Output
JSON array of objects with following structure:
- **name**: String. Name of the layer.
- **url**: String. URL of the layer. It points to [GET Layer](#get-layer).

## Layer
### URL
`/<user>/layers/<layername>`

### GET Layer
Get information about the layer.

#### Input parameters
None.
#### Output
JSON object with following structure:
- **name**: String. Layer name within user's workspace of GeoServer. It should be used for identifying layer within WMS and WFS endpoints.
- **title**: String.
- **description**: String.
- *status*: Status information about GeoServer import and availability of the layer. No status object = import was successfully completed and the layer is available.
- **wms**: String. URL of WMS endpoint. It points to WMS endpoint of user's workspace.
- **wfs**: String. URL of WFS endpoint. It points to WFS endpoint of user's workspace.
- **thumbnail**
  - *url*: String. URL of layer thumbnail. It points to [GET Layer Thumbnail](#get-layer-thumbnail).
  - *status*: Status information about generating and availability of thumbnail. No status object = thumbnail was successfully generated and it is available.
- **files**
  - **names**: Array of strings. Names of input vector data files that were imported to the DB table. Names are relative to user's directory.
  - *status*: Status information about saving and availability of files. No status object = all listed files were successfully saved.
- **db_table**
  - **name**: String. DB table name within PostgreSQL user's schema. This table is used as GeoServer source of layer.
  - *status*: Status information about DB import and availability of the table. No status object = import was successfully completed.



## Layer Thumbnail
### URL
`/<user>/layers/<layername>/thumbnail`
### GET Layer Thumbnail
Get thumbnail of the layer in PNG format, 300x300 px, transparent background.

#### Input parameters
None.
#### Output
PNG image.
