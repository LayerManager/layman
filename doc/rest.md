# REST API

## Overview
|Endpoint|URL|GET|POST|PATCH|DELETE|
|---|---|---|---|---|---|
|Layers|`/rest/<workspace_name>/layers`|[GET](#get-layers)| [POST](#post-layers) | x | [DELETE](#delete-layers) |
|[Layer](models.md#layer)|`/rest/<workspace_name>/layers/<layername>`|[GET](#get-layer)| x | [PATCH](#patch-layer) | [DELETE](#delete-layer) |
|Layer Thumbnail|`/rest/<workspace_name>/layers/<layername>/thumbnail`|[GET](#get-layer-thumbnail)| x | x | x |
|Layer Style|`/rest/<workspace_name>/layers/<layername>/style`|[GET](#get-layer-style)| x | x | x |
|Layer Chunk|`/rest/<workspace_name>/layers/<layername>/chunk`|[GET](#get-layer-chunk)| [POST](#post-layer-chunk) | x | x |
|Layer Metadata Comparison|`/rest/<workspace_name>/layers/<layername>/metadata-comparison`|[GET](#get-layer-metadata-comparison) | x | x | x |
|Maps|`/rest/<workspace_name>/maps`|[GET](#get-maps)| [POST](#post-maps) | x | [DELETE](#delete-maps) |
|[Map](models.md#map)|`/rest/<workspace_name>/maps/<mapname>`|[GET](#get-map)| x | [PATCH](#patch-map) | [DELETE](#delete-map) |
|Map File|`/rest/<workspace_name>/maps/<mapname>/file`|[GET](#get-map-file)| x | x | x |
|Map Thumbnail|`/rest/<workspace_name>/maps/<mapname>/thumbnail`|[GET](#get-map-thumbnail)| x | x | x |
|Map Metadata Comparison|`/rest/<workspace_name>/layers/<layername>/metadata-comparison`|[GET](#get-map-metadata-comparison) | x | x | x |
|Users|`/rest/users`|[GET](#get-users)| x | x | x |
|Current [User](models.md#user)|`/rest/current-user`|[GET](#get-current-user)| x | [PATCH](#patch-current-user) | [DELETE](#delete-current-user) |

#### REST path parameters
- **workspace_name**, string `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`
   - string identifying [workspace](models.md#workspace)


## Layers
### URL
`/rest/<workspace_name>/layers`

### GET Layers
Get list of published layers.

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON array of objects representing available layers with following structure:
- **name**: String. Name of the layer.
- **title**: String. Title of the layer.
- **uuid**: String. UUID of the layer.
- **url**: String. URL of the layer. It points to [GET Layer](#get-layer).
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization). If value is not specified, current user will be set if logged in, otherwise role EVERYONE.
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization). If value is not specified, only owner of workspace will be set for [personal workspaces](models.md#personal-workspace) and role EVERYONE for [public workspaces](models.md#public-workspace). If value is not specified, current user will be set if logged in, otherwise role EVERYONE.

### POST Layers
Publish vector data file as new layer of WMS and WFS.

Processing chain consists of few steps:
- save file to user directory within Layman data directory
- import the file to PostgreSQL database as new table into user schema, including geometry transformation to EPSG:3857
- publish the table as new layer (feature type) within user workspace of GeoServer
- generate thumbnail image
- publish metadata record to Micka
- save basic information (name, title, access_rights) into PostgreSQL

If user directory, database schema, GeoServer's workspace, or GeoServer's datastore does not exist yet, it is created on demand.

Response to this request may be returned sooner than the processing chain is finished to enable asynchronous processing. Status of processing chain can be seen using [GET Layer](#get-layer) and **status** properties of layer sources (wms, wfs, thumbnail, db_table, file, sld, metadata).

It is possible to upload data files asynchronously, which is suitable for large files. This can be done in three steps:
1. Send POST Layers request with **file** parameter filled by file names that you want to upload
2. Read set of files accepted to upload from POST Layers response, **files_to_upload** property. The set of accepted files will be either equal to or subset of file names sent in **file** parameter.
3. Send [POST Layer Chunk](#post-layer-chunk) requests using Resumable.js to upload files.

Check [Asynchronous file upload](async-file-upload.md) example.

#### Request
Content-Type: `multipart/form-data`, `application/x-www-form-urlencoded`

Body parameters:
- **file**, file(s) or file name(s)
   - one of following options is expected:
      - GeoJSON file
      - ShapeFile files (at least three files: .shp, .shx, .dbf)
      - file names, i.e. array of strings
   - if file names are provided, files must be uploaded subsequently using [POST Layer Chunk](#post-layer-chunk)
   - if published file has empty bounding box (i.e. no features), its bounding box on WMS/WFS endpoint is set to the whole World
- *name*, string
   - computer-friendly identifier of the layer
   - must be unique among all layers of one workspace
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
- *access_rights.read*, string
   - array of names of [users](./models.md#user) and [roles](./models.md#role) separated by comma (`,`)
   - these users or/and roles will get [read access](./security.md#Authorization) to this publication
- *access_rights.write*, string
   - array of names of [users](./models.md#user) and [roles](./models.md#role) separated by comma (`,`)
   - these users or/and roles will get [write access](./security.md#Authorization) to this publication

#### Response
Content-Type: `application/json`

JSON array of objects representing posted layers with following structure:
- **name**: String. Name of the layer.
- **uuid**: String. UUID of the layer.
- **url**: String. URL of the layer. It points to [GET Layer](#get-layer).
- *files_to_upload*: List of objects. It's present only if **file** parameter contained file names. Each object represents one file that server expects to be subsequently uploaded using [POST Layer Chunk](#post-layer-chunk). Each object has following properties:
   - **file**: name of the file, equal to one of file name from **file** parameter
   - **layman_original_parameter**: name of the request parameter that contained the file name; currently, the only possible value is `file`

### DELETE Layers
Delete existing layers and all associated sources, including vector data file and DB table for all layers in the workspace. It is possible to delete layers, whose publication process is still running. In such case, the publication process is aborted safely. Only layers on which user has [write access right](./security.md#access-to-multi-publication-endpoints) are deleted.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON array of objects representing deleted layers:
- **name**: String. Former name of the layer.
- **title**: String. Former title of the layer.
- **uuid**: String. Former UUID of the layer.
- **url**: String. Former URL of the layer. It points to [GET Layer](#get-layer).
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with former [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with former [write access](./security.md#Authorization).

## Layer
### URL
`/rest/<workspace_name>/layers/<layername>`

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
- **name**: String. Layername used for identification within Layman user workspace. It can be also used for identifying layer within WMS and WFS endpoints.
- **uuid**: String. UUID of the layer.
- **url**: String. URL pointing to this endpoint.
- **title**: String.
- **description**: String.
- **wms**
  - *url*: String. URL of WMS endpoint. It points to WMS endpoint of GeoServer user workspace.
  - *status*: Status information about GeoServer import and availability of WMS layer. No status object means the source is available. Usual state values are
    - PENDING: publishing of this source is queued, but it did not start yet
    - STARTED: publishing of this source is in process
    - FAILURE: publishing process failed
    - NOT_AVAILABLE: source is not available, e.g. because publishing process failed
  - *error*: If status is FAILURE, this may contain error object.
- **wfs**
  - *url*: String. URL of WFS endpoint. It points to WFS endpoint of GeoServer user workspace.
  - *status*: Status information about GeoServer import and availability of WFS feature type. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **thumbnail**
  - *url*: String. URL of layer thumbnail. It points to [GET Layer Thumbnail](#get-layer-thumbnail).
  - *status*: Status information about generating and availability of thumbnail. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **file**
  - *path*: String. Path to input vector data file that was imported to the DB table. Path is relative to user directory.
  - *status*: Status information about saving and availability of files. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **db_table**
  - **name**: String. DB table name within PostgreSQL user schema. This table is used as GeoServer source of layer.
  - *status*: Status information about DB import and availability of the table. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **sld**
  - **url**: String. URL of layer default style. It points to [GET Layer Style](#get-layer-style).
  - *status*: Status information about publishing SLD. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- *metadata*
  - *identifier*: String. Identifier of metadata record in CSW instance.
  - *record_url*: String. URL of metadata record accessible by web browser, probably with some editing capabilities.
  - *csw_url*: String. URL of CSW endpoint. It points to CSW endpoint of Micka.
  - *comparison_url*: String. URL of [GET Layer Metadata Comparison](#get-layer-metadata-comparison).
  - *status*: Status information about metadata import and availability. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).

### PATCH Layer
Update information about existing layer. First, it deletes sources of the layer, and then it publishes them again with new parameters. The processing chain is similar to [POST Layers](#post-layers).

Response to this request may be returned sooner than the processing chain is finished to enable asynchronous processing.

It is possible to upload data files asynchronously, which is suitable for large files. See [POST Layers](#post-layers).

#### Request
Content-Type: `multipart/form-data`, `application/x-www-form-urlencoded`

Parameters have same meaning as in case of [POST Layers](#post-layers).

Body parameters:
- *file*, file(s) or file name(s)
   - If provided, current layer vector data file will be deleted and replaced by this file. GeoServer layer, DB table, and thumbnail will be deleted and created again using the new file.
   - one of following options is expected:
      - GeoJSON file
      - ShapeFile files (at least three files: .shp, .shx, .dbf)
      - file names, i.e. array of strings
   - if file names are provided, files must be uploaded subsequently using [POST Layer Chunk](#post-layer-chunk)
   - if published file has empty bounding box (i.e. no features), its bounding box on WMS/WFS endpoint is set to the whole World
- *title*
- *description*
- *crs*, string `EPSG:3857` or `EPSG:4326`
   - Taken into account only if `file` is provided.
- *sld*, SLD file
   - If provided, current layer thumbnail will be temporarily deleted and created again using the new style.
- *access_rights.read*, string
   - array of names of [users](./models.md#user) and [roles](./models.md#role) separated by comma (`,`)
   - these users or/and roles will get [read access](./security.md#Authorization) to this publication
- *access_rights.write*, string
   - array of names of [users](./models.md#user) and [roles](./models.md#role) separated by comma (`,`)
   - these users or/and roles will get [write access](./security.md#Authorization) to this publication

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
`/rest/<workspace_name>/layers/<layername>/thumbnail`
### GET Layer Thumbnail
Get thumbnail of the layer in PNG format, 300x300 px, transparent background.

#### Request
No action parameters.
#### Response
Content-Type: `image/png`

PNG image.


## Layer Style
### URL
`/rest/<workspace_name>/layers/<layername>/style`
### GET Layer Style
Get default style of the layer in XML format. Request is redirected to GeoServer [/rest/workspaces/{workspace}/styles/{style}](https://docs.geoserver.org/latest/en/api/#1.0.0/styles.yaml). Anybody can call GET, nobody can call any other method. 

#### Request
No action parameters.
#### Response
Content-Type: `Application/xml`


## Layer Chunk
Layer Chunk endpoint enables to upload layer data files asynchronously by splitting them into small parts called *chunks* that are uploaded independently. The endpoint is expected to be operated using [Resumable.js](http://www.resumablejs.com/) library. Resumable.js can split and upload files by chunks using [HTML File API](https://developer.mozilla.org/en-US/docs/Web/API/File), widely [supported by major browsers](https://caniuse.com/#feat=fileapi).

Check [Asynchronous file upload](async-file-upload.md) example. 

The endpoint is activated after [POST Layers](#post-layers) or [PATCH Layer](#patch-layer) request if and only if the **file** parameter contained file name(s). The endpoint is active till first of the following happens:
- all file chunks are uploaded
- no chunk is uploaded within [UPLOAD_MAX_INACTIVITY_TIME](../src/layman_settings.py)
- layer is deleted

### URL
`/rest/<workspace_name>/layers/<layername>/chunk`
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


### GET Layer Metadata Comparison
Get comparison of metadata properties among Layman, CSW, WMS and WFS.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON object with one attribute:
- **metadata_sources**: Dictionary of objects. Key is ID of metadata source valid for this JSON only (not persistent in time!). Value is object with following attributes:
  - **url**: String. URL of the metadata source ([GET Layer](#get-layer), CSW record, WMS Capabilities, or WFS Capabitilities).
- **metadata_properties**: Dictionary of objects. Key is name of [metadata property](./metadata.md) (e.g. `reference_system`). Value is object with following attributes:
  - **values**: Dictionary of objects. Key is ID of metadata source corresponding with `metadata_sources` attribute. Value is any valid JSON (null, number, string, boolean, list, or object) representing value of [metadata property](./metadata.md) (e.g. `[3857, 4326]`). Null means the value is not set.
  - **equal**: Boolean. True if all values are considered equal, false otherwise.
  - **equal_or_null**: Boolean. True if all values are considered equal or null, false otherwise.


## Maps
### URL
`/rest/<workspace_name>/maps`

### GET Maps
Get list of published maps (map compositions).

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON array of objects representing available maps with following structure:
- **name**: String. Name of the map.
- **title**: String. Title of the map.
- **uuid**: String. UUID of the map.
- **url**: String. URL of the map. It points to [GET Map](#get-map).
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).

### POST Maps
Publish new map composition. Accepts JSON valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema) used by [Hslayers-ng](https://github.com/hslayers/hslayers-ng).

Processing chain consists of few steps:
- validate JSON file against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema)
- save file to user directory
- if needed, update some JSON attributes (`name`, `title`, or `abstract`)
- generate thumbnail image
- publish metadata record to Micka
- save basic information (name, title, access_rights) into PostgreSQL

If user directory does not exist yet, it is created on demand.

#### Request
Content-Type: `multipart/form-data`

Body parameters:
- **file**, JSON file
   - must be valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema)
- *name*, string
   - computer-friendly identifier of the map
   - must be unique among all maps of one workspace
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
- *access_rights.read*, string
   - array of names of [users](./models.md#user) and [roles](./models.md#role) separated by comma (`,`)
   - these users or/and roles will get [read access](./security.md#Authorization) to this publication
- *access_rights.write*, string
   - array of names of [users](./models.md#user) and [roles](./models.md#role) separated by comma (`,`)
   - these users or/and roles will get [write access](./security.md#Authorization) to this publication

#### Response
Content-Type: `application/json`

JSON array of objects representing posted maps with following structure:
- **name**: String. Name of the map.
- **uuid**: String. UUID of the map.
- **url**: String. URL of the map. It points to [GET Map](#get-map).

### DELETE Maps
Delete existing maps and all associated sources, including map-composition JSON file and map thumbnail for all mapss in the workspace. Only maps on which user has [write access right](./security.md#access-to-multi-publication-endpoints) are deleted.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON array of objects representing deleted maps:
- **name**: String. Former name of the map.
- **title**: String. Former title of the map.
- **uuid**: String. Former UUID of the map.
- **url**: String. Former URL of the map. It points to [GET Map](#get-map).
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with former [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with former [write access](./security.md#Authorization).

## Map
### URL
`/rest/<workspace_name>/maps/<mapname>`

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
- **name**: String. Mapname used for identification within Layman user workspace. Equal to `name` attribute of JSON root object
- **uuid**: String. UUID of the map.
- **url**: String. URL pointing to this endpoint.
- **title**: String. Taken from `title` attribute of JSON root object
- **description**: String. Taken from `abstract` attribute of JSON root object.
- **file**
  - *url*: String. URL of map-composition JSON file. It points to [GET Map File](#get-map-file).
  - *path*: String. Path to map-composition JSON file, relative to user directory.
  - *status*: Status information about availability of file. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **thumbnail**
  - *url*: String. URL of map thumbnail. It points to [GET Map Thumbnail](#get-map-thumbnail).
  - *status*: Status information about generating and availability of thumbnail. See [GET Layer](#get-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- *metadata*
  - *identifier*: String. Identifier of metadata record in CSW instance.
  - *record_url*: String. URL of metadata record accessible by web browser, probably with some editing capabilities.
  - *csw_url*: String. URL of CSW endpoint. It points to CSW endpoint of Micka.
  - *comparison_url*: String. URL of [GET Map Metadata Comparison](#get-map-metadata-comparison).
  - *status*: Status information about metadata import and availability. See [GET Map](#get-map) 
  - *error*: If status is FAILURE, this may contain error object.
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).

### PATCH Map
Update information about existing map. First, it deletes sources of the map, and then it publishes them again with new parameters. The processing chain is similar to [POST Maps](#post-maps).

#### Request
Content-Type: `multipart/form-data`, `application/x-www-form-urlencoded`

Parameters have same meaning as in case of [POST Maps](#post-maps).

Body parameters:
*file*, JSON file
   - If provided, thumbnail will be deleted and created again using the new file.
   - must be valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema)
- *title*, string `.+`
   - human readable name of the map
   - by default it is either `title` attribute of JSON root object or map name
- *description*, string `.+`
   - by default it is either `abstract` attribute of JSON root object or empty string
- *access_rights.read*, string
   - array of names of [users](./models.md#user) and [roles](./models.md#role) separated by comma (`,`)
   - these users or/and roles will get [read access](./security.md#Authorization) to this publication
- *access_rights.write*, string
   - array of names of [users](./models.md#user) and [roles](./models.md#role) separated by comma (`,`)
   - these users or/and roles will get [write access](./security.md#Authorization) to this publication

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
`/rest/<workspace_name>/maps/<mapname>/file`
### GET Map File
Get JSON file describing the map valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema).

Notice that some JSON properties are automatically updated by layman, so file obtained by this endpoint may be slightly different from file that was uploaded. Expected changes:
- **name** set to `<mapname>` in URL of this endpoint
- **title** obtained from [POST Maps](#post-maps) or [PATCH Map](#patch-map) as `title`
- **abstract** obtained from [POST Maps](#post-maps) or [PATCH Map](#patch-map) as `description`
- **user** updated on the fly during this request:
   - **name** set to `<workspace_name>` in URL of this endpoint
   - **email** set to email of the owner, or empty string if not known
   - other properties will be deleted
- **groups** are removed

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON file describing the map valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema).


## Map Thumbnail
### URL
`/rest/<workspace_name>/maps/<mapname>/thumbnail`
### GET Map Thumbnail
Get thumbnail of the map in PNG format, 300x300 px, transparent background.

#### Request
No action parameters.
#### Response
Content-Type: `image/png`

PNG image.


### GET Map Metadata Comparison
Get comparison of metadata properties among Layman and CSW.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON object with one attribute:
- **metadata_sources**: Dictionary of objects. Key is ID of metadata source valid for this JSON only (not persistent in time!). Value is object with following attributes:
  - **url**: String. URL of the metadata source ([GET Map](#get-map), [GET Map File](#get-map-file), or CSW record).
- **metadata_properties**: Dictionary of objects. Key is name of [metadata property](./metadata.md) (e.g. `reference_system`). Value is object with following attributes:
  - **values**: Dictionary of objects. Key is ID of metadata source corresponding with `metadata_sources` attribute. Value is any valid JSON (null, number, string, boolean, list, or object) representing value of [metadata property](./metadata.md) (e.g. `[3857, 4326]`). Null means the value is not set.
  - **equal**: Boolean. True if all values are considered equal, false otherwise.
  - **equal_or_null**: Boolean. True if all values are considered equal or null, false otherwise.


## Users
### URL
`/rest/users`

### GET Users
Get list of registered users.

#### Request.
No action parameters.

#### Response
Content-Type: `application/json`

JSON array of objects representing users of Layman with following structure:
- **username**: String. Username of the user.
- **screen_name**: String. Screen name of the user.
- **given_name**: String. Given name of the user.
- **family_name**: String. Family name of the user
- **middle_name**: String. Middle name of the user
- **name**: String. Whole name of the user (given_name + middle_name + family_name).

## Current User
### URL
`/rest/current-user`

### GET Current User
Get information about current user.

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON object with following structure:
- **authenticated**: Boolean. `true` if user is authenticated, `false` if user is anonymous.
- **claims**: Object. Dictionary of known claims (e.g. name, nickname, preferred_username, or email). Claims are inspired by and have same meaning as [OpenID Connect standard claims](https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims). Some claims are set even if the user is anonymous (e.g. name).
- *username*: String. [Username](models.md#username) the user reserved within Layman. If not set, it was not reserved yet. To be used as username in some REST API paths (i.e. `/rest/<username>/...`)

### PATCH Current User
Update information about current user. Currently used only for reserving `username`.

#### Request
Content-Type: `application/x-www-form-urlencoded`

Query parameters:
- *adjust_username*: String.
  - `false` (default): If `username` sent in body parameter is already reserved by another user, Layman will return error.
  - `true`: If `username` sent in body parameter is already reserved by another user or `username` is an empty string, layman will definitely reserve some `username`, preferably similar to the value sent in `username` body parameter or to one of claims.

Body parameters:
- *username*: String. [Username](models.md#username) that should be reserved for current user. Username can be reserved only once and it cannot be changed. See URL parameter `adjust_username` for other details.

#### Response
Content-Type: `application/json`

JSON object, same as in case of [GET](#get-current-user).

### DELETE Current User
Deletes current authentication credentials from Layman's cache. This should be called when user logs out from client.

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

HTTP status code 200 if credentials were deleted.
