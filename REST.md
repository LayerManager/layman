# REST API

## Files
### URL
`/files`
### POST
Upload new file.

#### Input parameters
- **user**
   - owner of the file
- **file**
- **name** [aplhanunmeric characters or _]
   - must be unique within one use
- **title**
- **crs**, EPSG code
- **description**
- **sld**

#### Output
- **file_name**
- **layer_name**
   - including namespace
- **wms**
   - URL of WMS endpoint
- **wfs**
   - URL of WFS endpoint
- **thumbnail**
