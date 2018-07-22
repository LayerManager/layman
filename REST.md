# REST API

## Layers
### URL
`/layers`
### POST
Publish vector data file as new layer of WMS and WFS.

Processing chain consists of few steps:
- save file to user's directory within GeoServer data directory
- import the file to PostgreSQL database as new table into user's schema
- publish the table as new layer (feature type) within user's workspace of GeoServer
- generate thumbnail image

If user's directory, database schema, or GeoServer's worskpace does not exist yet, it is created on demand.

#### Input parameters
- **user**, string `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`
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
   - by default it is layer_name
- *description*
   - by default it is empty string
- *crs*, string `EPSG:3857` or `EPSG:4326`
   - by default it is read/guessed from input file
- *sld*, SLD file
   - by default default SLD style of GeoServer is used

#### Output
- **file_name**
   - within user's directory
- **table_name**
   - within PostgreSQL user's schema
- **layer_name**
   - within user's workspace of GeoServer
   - should be used for identifying layer within WMS and WFS
- **wms**
   - URL of WMS endpoint
   - points to user's workspace WMS endpoint
- **wfs**
   - URL of WFS endpoint
   - points to user's workspace WFS endpoint
- **thumbnail**
   - base64 encoded PNG usable for HTML `img` `src` attribute
