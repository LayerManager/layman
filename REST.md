# REST API

## Layers
### URL
`/layers`
### POST
Upload new layer.

#### Input parameters
- **user**, string `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`
   - owner of the file
- **file**, file
   - GeoJSON file
- *name*, string
   - computer-friendly identifier of the layer
   - must be unique within one user
   - by default, it is file name without extension
   - will be automatically adjusted using `to_safe_layer_name` function
- *title*, string `.+`
   - by default it is name (if set) or file name without extension
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
   - points to user's workspace
- **wfs**
   - URL of WFS endpoint
   - points to user's workspace
- **thumbnail**
   - base64 encoded PNG usable for HTML `img` `src` attribute
