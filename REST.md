# REST API

## Files
### URL
`/files/<user>`
### POST
Upload new file.

#### Input parameters
- **\<user\>**, string `\w+`
   - owner of the file
- **file**, file
- **name**, string `\w+`
   - must be unique within one user
- **title**, string `.+`
- **description**
- **crs**, EPSG code
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
