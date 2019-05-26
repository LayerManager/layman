# REST API

## Overview
|Endpoint|URL|GET|POST|PATCH|DELETE|
|---|---|---|---|---|---|
|Layers|`/rest/<user>/layers`|[GET](#get-layers)| [POST](#post-layers) | x | x |
|Layer|`/rest/<user>/layers/<layername>`|[GET](#get-layer)| x | [PATCH](#patch-layer) | [DELETE](#delete-layer) |
|Layer Thumbnail|`/rest/<user>/layers/<layername>/thumbnail`|[GET](#get-layer-thumbnail)| x | x | x |
|Layer Chunk|`/rest/<user>/layers/<layername>/chunk`|[GET](#get-layer-chunk)| [POST](#post-layer-chunk) | x | x |
|Maps|`/rest/<user>/maps`|[GET](#get-maps)| [POST](#post-maps) | x | x |
|Map|`/rest/<user>/maps/<mapname>`|[GET](#get-map)| x | [PATCH](#patch-map) | [DELETE](#delete-map) |
|Map File|`/rest/<user>/maps/<mapname>/file`|[GET](#get-map-file)| x | x | x |
|Map Thumbnail|`/rest/<user>/maps/<mapname>/thumbnail`|[GET](#get-map-thumbnail)| x | x | x |

#### REST path parameters
- **user**, string `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`
   - owner of the layer
   - it can be almost any string matching the regular expression (some keywords are not allowed)
   - it is not real user of file system, DB, or GeoServer


## Layers
### URL
`/rest/<user>/layers`

### GET Layers
Get list of published layers.

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON array of objects representing available layers with following structure:
- **name**: String. Name of the layer.
- **uuid**: String. UUID of the layer.
- **url**: String. URL of the layer. It points to [GET Layer](#get-layer).

### POST Layers
Publish vector data file as new layer of WMS and WFS.

Processing chain consists of few steps:
- save file to user's directory within GeoServer data directory
- import the file to PostgreSQL database as new table into user's schema, including geometry transformation to EPSG:3857
- publish the table as new layer (feature type) within user's workspace of GeoServer
- generate thumbnail image

If user's directory, database schema, GeoServer's worskpace, or GeoServer's store does not exist yet, it is created on demand.

Response to this request may be returned sooner than the processing chain is finished to enable asynchronous processing. Status of processing chain can be seen using [GET Layer](#get-layer) and **status** properties of layer sources (wms, wfs, thumbnail, db_table, file, sld).

It is possible to upload data files asynchronously, which is suitable for large files. This can be done in three steps:
1. Send POST Layers request with **file** parameter filled by file names that you want to upload
2. Read set of files accepted to upload from POST Layers response, **files_to_upload** property. The set of accepted files will be either equal to or subset of file names sent in **file** parameter.
3. Send [POST Layer Chunk](#post-layer-chunk) requests using Resumable.js to upload files.

Check [Asynchronous file upload](async-file-upload.md) example.

#### Request
Content-Type: `multipart/form-data`

Body parameters:
- **file**, file(s) or file name(s)
   - one of following options is expected:
      - GeoJSON file
      - ShapeFile files (at least three files: .shp, .shx, .dbf)
      - file names, i.e. array of strings
   - if file names are provided, files must be uploaded subsequently using [POST Layer Chunk](#post-layer-chunk)
- *name*, string
   - computer-friendly identifier of the layer
   - must be unique within one user
   - by default, it is file name without extension
   - will be automatically adjusted using `to_safe_layer_name` function
- *title*, string `.+`
   - human readable name of the layer
   - by default it is layer name
- *description*
   - by default it is empty string
- *crs*, string `EPSG:3857` or `EPSG:4326`
   - CRS of the file
   - by default it is read/guessed from input file
- *sld*, SLD file
   - by default default SLD style of GeoServer is used
   - uploading of additional style files, e.g. point-symbol images or fonts is not supported

#### Response
Content-Type: `application/json`

JSON array of objects representing posted layers with following structure:
- **name**: String. Name of the layer.
- **uuid**: String. UUID of the layer.
- **url**: String. URL of the layer. It points to [GET Layer](#get-layer).
- *files_to_upload*: List of objects. It's present only if **file** parameter contained file names. Each object represents one file that server expects to be subsequently uploaded using [POST Layer Chunk](#post-layer-chunk). Each object has following properties:
   - **file**: name of the file, equal to one of file name from **file** parameter
   - **layman_original_parameter**: name of the request parameter that contained the file name; currently, the only possible value is `file`


## Layer
### URL
`/rest/<user>/layers/<layername>`

#### Endpoint path parameters
- **layername**
   - layer name used for identification
   - it can be obtained from responses of [GET Layers](#get-layers), [POST Layers](#post-layers), and all responses of this endpoint

### GET Layer
Get information about existing layer.

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON object with following structure:
- **name**: String. Layer name within user's workspace of GeoServer. It should be used for identifying layer within WMS and WFS endpoints.
- **uuid**: String. UUID of the layer.
- **url**: String. URL pointing to this endpoint.
- **title**: String.
- **description**: String.
- **wms**
  - *url*: String. URL of WMS endpoint. It points to WMS endpoint of user's workspace.
  - *status*: Status information about GeoServer import and availability of WMS layer. No status object means the source is available. Usual state values are
    - PENDING: publishing of this source is queued, but it did not start yet
    - STARTED: publishing of this source is in process
    - FAILURE: publishing process failed
    - NOT_AVAILABLE: source is not available, e.g. because publishing process failed
  - *error*: If status is FAILURE, this may contain error object.
- **wfs**
  - *url*: String. URL of WFS endpoint. It points to WFS endpoint of user's workspace.
  - *status*: Status information about GeoServer import and availability of WFS feature type. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **thumbnail**
  - *url*: String. URL of layer thumbnail. It points to [GET Layer Thumbnail](#get-layer-thumbnail).
  - *status*: Status information about generating and availability of thumbnail. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **file**
  - *path*: String. Path to input vector data file that was imported to the DB table. Path is relative to user's directory.
  - *status*: Status information about saving and availability of files. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **db_table**
  - **name**: String. DB table name within PostgreSQL user's schema. This table is used as GeoServer source of layer.
  - *status*: Status information about DB import and availability of the table. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- *sld*
  - **status**: Status information about publishing SLD. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.

### PATCH Layer
Update information about existing layer. First, it deletes sources of the layer, and then it publishes them again with new parameters. The processing chain is similar to [POST Layers](#post-layers).

Response to this request may be returned sooner than the processing chain is finished to enable asynchronous processing.

It is possible to upload data files asynchronously, which is suitable for large files. See [POST Layers](#post-layers).

#### Request
Content-Type: `multipart/form-data`

Parameters have same meaning as in case of [POST Layers](#post-layers).

Body parameters:
- *file*, file(s) or file name(s)
   - If provided, current layer vector data file will be deleted and replaced by this file. GeoServer layer, DB table, and thumbnail will be deleted and created again using the new file.
   - one of following options is expected:
      - GeoJSON file
      - ShapeFile files (at least three files: .shp, .shx, .dbf)
      - file names, i.e. array of strings
   - if file names are provided, files must be uploaded subsequently using [POST Layer Chunk](#post-layer-chunk)
- *title*
- *description*
- *crs*, string `EPSG:3857` or `EPSG:4326`
   - Taken into account only if `file` is provided.
- *sld*, SLD file
   - If provided, current layer thumbnail will be temporarily deleted and created again using the new style.

#### Response
Content-Type: `application/json`

JSON object, same as in case of [GET](#get-layer), possibly extended with one extra property:
- *files_to_upload*: List of objects. It's present only if **file** parameter contained file names. See [POST Layers](#post-layers) response to find out more.

### DELETE Layer
Delete existing layer and all associated sources, including vector data file and DB table. It is possible to delete layer, whose publication process is still running. In such case, the publication process is aborted safely.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON object representing deleted layer:
- **name**: String. Former name of the layer.
- **uuid**: String. Former UUID of the layer.
- **url**: String. Former URL of the layer. It points to [GET Layer](#get-layer).


## Layer Thumbnail
### URL
`/rest/<user>/layers/<layername>/thumbnail`
### GET Layer Thumbnail
Get thumbnail of the layer in PNG format, 300x300 px, transparent background.

#### Request
No action parameters.
#### Response
Content-Type: `image/png`

PNG image.


## Layer Chunk
Layer Chunk endpoint enables to upload layer data files asynchronously by splitting them into small parts called *chunks* that are uploaded independently. The endpoint is expected to be operated using [Resumable.js](http://www.resumablejs.com/) library. Resumable.js can split and upload files by chunks using [HTML File API](https://developer.mozilla.org/en-US/docs/Web/API/File), widely [supported by major browsers](https://caniuse.com/#feat=fileapi).

Check [Asynchronous file upload](async-file-upload.md) example. 

The endpoint is activated after [POST Layers](#post-layers) or [PATCH Layer](#patch-layer) request if and only if the **file** parameter contained file name(s). The endpoint is active till first of the following happens:
- all file chunks are uploaded
- no chunk is uploaded within [UPLOAD_MAX_INACTIVITY_TIME](src/layman_settings.py)
- layer is deleted

### URL
`/rest/<username>/layers/<layername>/chunk`
### GET Layer Chunk
Test if file chunk is already uploaded on the server.

#### Request
Query parameters:
- **layman_original_parameter**, name of parameter of preceding request ([POST Layers](#post-layers) or [PATCH Layer](#patch-layer)) that contained the file name
- **resumableFilename**, name of file whose chunk is requested
- **resumableChunkNumber**, serial number of requested chunk

#### Response
Content-Type: `application/json`

HTTP status code 200 if chunk is already uploaded on the server, otherwise 404.

### POST Layer Chunk
Upload file chunk to the server.

#### Request
Content-Type: `multipart/form-data`

Body parameters:
- **file**, uploaded chunk
- **resumableChunkNumber**, serial number of uploaded chunk
- **resumableFilename**, name of file whose chunk is uploaded
- **layman_original_parameter**, name of parameter of preceding request ([POST Layers](#post-layers) or [PATCH Layer](#patch-layer)) that contained the file name
- **resumableTotalChunks**, number of chunks the file is split to

#### Response
Content-Type: `application/json`

HTTP status code 200 if chunk was successfully saved.


## Maps
### URL
`/rest/<user>/maps`

### GET Maps
Get list of published maps (map compositions).

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON array of objects representing available maps with following structure:
- **name**: String. Name of the map.
- **uuid**: String. UUID of the map.
- **url**: String. URL of the map. It points to [GET Map](#get-map).

### POST Maps
Publish new map composition. Accepts JSON valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema) used by [Hslayers-ng](https://github.com/hslayers/hslayers-ng).

Processing chain consists of few steps:
- validate JSON file against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema)
- save file to user's directory
- if needed, update some JSON attributes (`name`, `title`, or `abstract`)
- generate thumbnail image

If user's directory does not exist yet, it is created on demand.

#### Request
Content-Type: `multipart/form-data`

Body parameters:
- **file**, JSON file
   - must be valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema)
- *name*, string
   - computer-friendly identifier of the map
   - must be unique within one user
   - by default, it is the first available of following options:
      - `name` attribute of JSON root object
      - `title` attribute of JSON root object
      - file name without extension
   - will be automatically adjusted using `to_safe_map_name` function
- *title*, string `.+`
   - human readable name of the map
   - by default it is either `title` attribute of JSON root object or map name
- *description*
   - by default it is either `abstract` attribute of JSON root object or empty string

#### Response
Content-Type: `application/json`

JSON array of objects representing posted maps with following structure:
- **name**: String. Name of the map.
- **uuid**: String. UUID of the map.
- **url**: String. URL of the map. It points to [GET Map](#get-map).


## Map
### URL
`/rest/<user>/maps/<mapname>`

#### Endpoint path parameters
- **mapname**
   - map name used for identification
   - it can be obtained from responses of [GET Maps](#get-maps), [POST Maps](#post-maps), and all responses of this endpoint

### GET Map
Get information about existing map.

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON object with following structure:
- **name**: String. Map name used for identification within user's namespace. Equal to `name` attribute of JSON root object
- **uuid**: String. UUID of the map.
- **url**: String. URL pointing to this endpoint.
- **title**: String. Taken from `title` attribute of JSON root object
- **description**: String. Taken from `abstract` attribute of JSON root object.
- **file**
  - *url*: String. URL of map-composition JSON file. It points to [GET Map File](#get-map-file).
  - *path*: String. Path to map-composition JSON file, relative to user's directory.
  - *status*: Status information about availability of file. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **thumbnail**
  - *url*: String. URL of map thumbnail. It points to [GET Map Thumbnail](#get-map-thumbnail).
  - *status*: Status information about generating and availability of thumbnail. See GET Map **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.

### PATCH Map
Update information about existing map. First, it deletes sources of the map, and then it publishes them again with new parameters. The processing chain is similar to [POST Maps](#post-maps).

#### Request
Content-Type: `multipart/form-data`

Parameters have same meaning as in case of [POST Maps](#post-maps).

Body parameters:
- *file*, JSON file
   - must be valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema)
- *title*, string `.+`
   - human readable name of the map
   - by default it is either `title` attribute of JSON root object or map name
- *description*, string `.+`
   - by default it is either `abstract` attribute of JSON root object or empty string

#### Response
Content-Type: `application/json`

JSON object, same as in case of [GET](#get-map).

### DELETE Map
Delete existing map and all associated sources, including map-composition JSON file and map thumbnail.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON object representing deleted map:
- **name**: String. Former name of the map.
- **uuid**: String. Former UUID of the map.
- **url**: String. Former URL of the map. It points to [GET Map](#get-map).


## Map File
### URL
`/rest/<user>/maps/<mapname>/file`
### GET Map File
Get JSON file describing the map valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema).

Notice that some JSON properties are automatically updated by layman, so file obtained by this endpoint may be slightly different from file that was uploaded. Expected changes:
- **name** set to `<mapname>` in URL of this endpoint
- **title** obtained from [POST Maps](#post-maps) or [PATCH Map](#patch-map) as `title`
- **abstract** obtained from [POST Maps](#post-maps) or [PATCH Map](#patch-map) as `description`
- **user** updated on the fly during this request:
   - **name** set to `<username>` in URL of this endpoint
   - **email** set to empty string (because Layman is not yet connected to any authorization system)
   - other properties will be deleted
- **groups** updated on the fly during this request:
   - **guest** set to `"w"` (because Layman is not yet connected to any authorization system and all REST endpoints are accessible to anyone)
   - other properties will be deleted

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON file describing the map valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema).


## Map Thumbnail
### URL
`/rest/<user>/maps/<mapname>/thumbnail`
### GET Map Thumbnail
Get thumbnail of the map in PNG format, 300x300 px, transparent background.

#### Request
No action parameters.
#### Response
Content-Type: `image/png`

PNG image.


