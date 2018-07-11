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
- **name**, string
   - computer-friendly identifier of the layer
   - must be unique within one user
   - will be automatically adjusted using `to_safe_layer_name` function
- **title**, string `.+`
- **description**
- **crs**, string `EPSG:3857` or `EPSG:4326`
- **sld**, SLD file

#### Output
- **file_name**
- **layer_name**
   - including namespace
- **wms**
   - URL of WMS endpoint
- **wfs**
   - URL of WFS endpoint
- **thumbnail**
