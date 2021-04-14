# REST API

## Overview
|Endpoint|URL|GET|POST|PATCH|DELETE|
|---|---|---|---|---|---|
|Layers|`/rest/layers`|[GET](#get-layers)| x | x | x |
|Workspace Layers|`/rest/workspaces/<workspace_name>/layers`|[GET](#get-workspace-layers)| [POST](#post-workspace-layers) | x | [DELETE](#delete-workspace-layers) |
|[Workspace Layer](models.md#layer)|`/rest/workspaces/<workspace_name>/layers/<layername>`|[GET](#get-workspace-layer)| x | [PATCH](#patch-workspace-layer) | [DELETE](#delete-workspace-layer) |
|Workspace Layer Thumbnail|`/rest/workspaces/<workspace_name>/layers/<layername>/thumbnail`|[GET](#get-workspace-layer-thumbnail)| x | x | x |
|Workspace Layer Style|`/rest/workspaces/<workspace_name>/layers/<layername>/style`|[GET](#get-workspace-layer-style)| x | x | x |
|Workspace Layer Chunk|`/rest/workspaces/<workspace_name>/layers/<layername>/chunk`|[GET](#get-workspace-layer-chunk)| [POST](#post-workspace-layer-chunk) | x | x |
|Workspace Layer Metadata Comparison|`/rest/workspaces/<workspace_name>/layers/<layername>/metadata-comparison`|[GET](#get-workspace-layer-metadata-comparison) | x | x | x |
|Maps|`/rest/maps`|[GET](#get-maps)| x | x | x |
|Workspace Maps|`/rest/workspaces/<workspace_name>/maps`|[GET](#get-workspace-maps)| [POST](#post-workspace-maps) | x | [DELETE](#delete-workspace-maps) |
|[Workspace Map](models.md#map)|`/rest/workspaces/<workspace_name>/maps/<mapname>`|[GET](#get-workspace-map)| x | [PATCH](#patch-workspace-map) | [DELETE](#delete-workspace-map) |
|Workspace Map File|`/rest/workspaces/<workspace_name>/maps/<mapname>/file`|[GET](#get-workspace-map-file)| x | x | x |
|Workspace Map Thumbnail|`/rest/workspaces/<workspace_name>/maps/<mapname>/thumbnail`|[GET](#get-workspace-map-thumbnail)| x | x | x |
|Workspace Map Metadata Comparison|`/rest/workspaces/<workspace_name>/layers/<layername>/metadata-comparison`|[GET](#get-workspace-map-metadata-comparison) | x | x | x |
|Users|`/rest/users`|[GET](#get-users)| x | x | x |
|Current [User](models.md#user)|`/rest/current-user`|[GET](#get-current-user)| x | [PATCH](#patch-current-user) | [DELETE](#delete-current-user) |
|Version|`/rest/about/version`|[GET](#get-version)| x | x | x |

#### REST path parameters
- **workspace_name**, string `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`
   - string identifying [workspace](models.md#workspace)
  
**_NOTE:_** Before version 1.10.0, workspace-related endpoints did not include `/workspaces` in their path. These old endpoints are still functional, but deprecated. More specifically, they return HTTP header **Deprecation**. If you get such header in response, rewrite your client to use new endpoint path. Old endpoints will stop working in the next major release.

## Layers
### URL
`/rest/layers`

### GET Layers
Get list of published layers.

#### Request
Query parameters:
- *full_text_filter*: String. List of words separated by space. Only layers with at least one of them in title will be returned. Search is case-insensitive, unaccent and did lemmatization for English. By default, layers are ordered by search rank in response if this filter is used.
- *bbox_filter*: String. Bounding box in EPSG:3857 defined by four comma-separated coordinates `minx,miny,maxx,maxy`. Only layers whose bounding box intersects with given bounding box will be returned.
- *order_by*: String. Can be one of these values:
  - `full_text` Publications will be ordered by results of full-text search. Can be used only in combination with *full_text_filter*.
  - `title` Publications will be ordered lexicographically by title value.
  - `last_change` Publications will be ordered by time of last change. Recently updated publications will be first.

#### Response
Content-Type: `application/json`

JSON array of objects representing available layers with following structure:
- **workspace**: String. Name of the layer's workspace.
- **name**: String. Name of the layer.
- **title**: String. Title of the layer.
- **uuid**: String. UUID of the layer.
- **url**: String. URL of the layer. It points to [GET Workspace Layer](#get-workspace-layer).
- **updated_at**: String. Date and time of last POST/PATCH of the publication. Format is [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601), more specifically `YYYY-MM-DDThh:mm:ss.sss±hh:mm`, always in UTC. Sample value: `"2021-03-18T09:29:53.769233+00:00"`
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).
- **bounding_box**: List of 4 floats. Bounding box coordinates [minx, miny, maxx, maxy] in EPSG:3857.

## Workspace Layers
### URL
`/rest/workspaces/<workspace_name>/layers`

### GET Workspace Layers
Get list of published layers.

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON array of objects representing available layers with following structure:
- **workspace**: String. Name of the layer's workspace.
- **name**: String. Name of the layer.
- **title**: String. Title of the layer.
- **uuid**: String. UUID of the layer.
- **url**: String. URL of the layer. It points to [GET Workspace Layer](#get-workspace-layer).
- **updated_at**: String. Date and time of last POST/PATCH of the publication. Format is [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601), more specifically `YYYY-MM-DDThh:mm:ss.sss±hh:mm`, always in UTC. Sample value: `"2021-03-18T09:29:53.769233+00:00"`
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).
- **bounding_box**: List of 4 floats. Bounding box coordinates [minx, miny, maxx, maxy] in EPSG:3857.

### POST Workspace Layers
Publish vector data file as new layer of WMS and WFS.

Processing chain consists of few steps:
- save file to workspace directory within Layman data directory
- import the file to PostgreSQL database as new table into workspace schema, including geometry transformation to EPSG:3857
- publish the table as new layer (feature type) within appropriate WFS workspaces of GeoServer
- for layers with SLD or none style:
  - publish the table as new layer (feature type) within appropriate WMS workspaces of GeoServer
- else for layers with QML style:
  - create QGS file on QGIS server filesystem with appropriate style
  - publish the layer on GeoServer through WMS cascade from QGIS server
- generate thumbnail image
- publish metadata record to Micka (it's public if and only if read access is set to EVERYONE)
- save basic information (name, title, access_rights) into PostgreSQL

If workspace directory, database schema, GeoServer's workspaces, or GeoServer's datastores does not exist yet, it is created on demand.

Response to this request may be returned sooner than the processing chain is finished to enable asynchronous processing. Status of processing chain can be seen using [GET Workspace Layer](#get-workspace-layer) and **status** properties of layer sources (wms, wfs, thumbnail, db_table, file, style, metadata).

It is possible to upload data files asynchronously, which is suitable for large files. This can be done in three steps:
1. Send POST Workspace Layers request with **file** parameter filled by file names that you want to upload
2. Read set of files accepted to upload from POST Workspace Layers response, **files_to_upload** property. The set of accepted files will be either equal to or subset of file names sent in **file** parameter.
3. Send [POST Workspace Layer Chunk](#post-workspace-layer-chunk) requests using Resumable.js to upload files.

Check [Asynchronous file upload](async-file-upload.md) example.

#### Request
Content-Type: `multipart/form-data`, `application/x-www-form-urlencoded`

Body parameters:
- **file**, file(s) or file name(s)
   - one of following options is expected:
      - GeoJSON file
      - ShapeFile files (at least three files: .shp, .shx, .dbf)
      - file names, i.e. array of strings
   - if file names are provided, files must be uploaded subsequently using [POST Workspace Layer Chunk](#post-workspace-layer-chunk)
   - if published file has empty bounding box (i.e. no features), its bounding box on WMS/WFS endpoint is set to the whole World
   - attribute names are [laundered](https://gdal.org/drivers/vector/pg.html#layer-creation-options) to be safely stored in DB
   - if QML style is used in this request, it must list all attributes contained in given data file
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
- *style*, style file
   - by default default SLD style of GeoServer is used
   - SLD or QML style file (recognized by the root element of XML: `StyledLayerDescriptor` or `qgis`)
   - uploading of additional style files, e.g. point-symbol images or fonts is not supported
   - attribute names are [laundered](https://gdal.org/drivers/vector/pg.html#layer-creation-options) to be in line with DB attribute names
- *access_rights.read*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [read access](./security.md#publication-access-rights) to this publication
   - default value is current authenticated user, or EVERYONE if published by anonymous
- *access_rights.write*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [write access](./security.md#publication-access-rights) to this publication
   - default value is current authenticated user, or EVERYONE if published by anonymous
- ~~sld~~, SLD file
   - **deprecated parameter**
   - alias for *style* parameter

#### Response
Content-Type: `application/json`

JSON array of objects representing posted layers with following structure:
- **name**: String. Name of the layer.
- **uuid**: String. UUID of the layer.
- **url**: String. URL of the layer. It points to [GET Workspace Layer](#get-workspace-layer).
- *files_to_upload*: List of objects. It's present only if **file** parameter contained file names. Each object represents one file that server expects to be subsequently uploaded using [POST Workspace Layer Chunk](#post-workspace-layer-chunk). Each object has following properties:
   - **file**: name of the file, equal to one of file name from **file** parameter
   - **layman_original_parameter**: name of the request parameter that contained the file name; currently, the only possible value is `file`

### DELETE Workspace Layers
Delete existing layers and all associated sources, including vector data file and DB table for all layers in the workspace. It is possible to delete layers, whose publication process is still running. In such case, the publication process is aborted safely. Only layers on which user has [write access right](./security.md#access-to-multi-publication-endpoints) are deleted.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON array of objects representing deleted layers:
- **name**: String. Former name of the layer.
- **title**: String. Former title of the layer.
- **uuid**: String. Former UUID of the layer.
- **url**: String. Former URL of the layer. It points to [GET Workspace Layer](#get-workspace-layer).
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with former [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with former [write access](./security.md#Authorization).

## Workspace Layer
### URL
`/rest/workspaces/<workspace_name>/layers/<layername>`

#### Endpoint path parameters
- **layername**
   - layer name used for identification
   - it can be obtained from responses of [GET Workspace Layers](#get-workspace-layers), [POST Workspace Layers](#post-workspace-layers), and all responses of this endpoint

### GET Workspace Layer
Get information about existing layer.

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON object with following structure:
- **name**: String. Layername used for identification within given [workspace](models.md#workspace). It can be also used for identifying layer within WMS and WFS endpoints.
- **uuid**: String. UUID of the layer.
- **url**: String. URL pointing to this endpoint.
- **title**: String.
- **description**: String.
- **updated_at**: String. Date and time of last POST/PATCH of the publication. Format is [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601), more specifically `YYYY-MM-DDThh:mm:ss.sss±hh:mm`, always in UTC. Sample value: `"2021-03-18T09:29:53.769233+00:00"`
- **wms**
  - *url*: String. URL of WMS endpoint. It points to WMS endpoint of appropriate GeoServer workspace.
  - *status*: Status information about GeoServer import and availability of WMS layer. No status object means the source is available. Usual state values are
    - PENDING: publishing of this source is queued, but it did not start yet
    - STARTED: publishing of this source is in process
    - FAILURE: publishing process failed
    - NOT_AVAILABLE: source is not available, e.g. because publishing process failed
  - *error*: If status is FAILURE, this may contain error object.
- **wfs**
  - *url*: String. URL of WFS endpoint. It points to WFS endpoint of appropriate GeoServer workspace.
  - *status*: Status information about GeoServer import and availability of WFS feature type. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **thumbnail**
  - *url*: String. URL of layer thumbnail. It points to [GET Workspace Layer Thumbnail](#get-workspace-layer-thumbnail).
  - *status*: Status information about generating and availability of thumbnail. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **file**
  - *path*: String. Path to input vector data file that was imported to the DB table. Path is relative to workspace directory.
  - *status*: Status information about saving and availability of files. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **db_table**
  - *name*: String. DB table name within PostgreSQL workspace schema. This table is used as GeoServer source of layer.
  - *status*: Status information about DB import and availability of the table. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **style**
  - *url*: String. URL of layer default style. It points to [GET Workspace Layer Style](#get-workspace-layer-style).
  - *type*: String. Type of used style. Either 'sld' or 'qml'.
  - *status*: Status information about publishing style. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **~~style~~**
  - **Deprecated**
  - Replaced by **style**, contains same info
- *metadata*
  - *identifier*: String. Identifier of metadata record in CSW instance.
  - *record_url*: String. URL of metadata record accessible by web browser, probably with some editing capabilities.
  - *csw_url*: String. URL of CSW endpoint. It points to CSW endpoint of Micka.
  - *comparison_url*: String. URL of [GET Workspace Layer Metadata Comparison](#get-workspace-layer-metadata-comparison).
  - *status*: Status information about metadata import and availability. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).
- **bounding_box**: List of 4 floats. Bounding box coordinates [minx, miny, maxx, maxy] in EPSG:3857.

### PATCH Workspace Layer
Update information about existing layer. First, it deletes sources of the layer, and then it publishes them again with new parameters. The processing chain is similar to [POST Workspace Layers](#post-workspace-layers).

Response to this request may be returned sooner than the processing chain is finished to enable asynchronous processing.

It is possible to upload data files asynchronously, which is suitable for large files. See [POST Workspace Layers](#post-workspace-layers).

#### Request
Content-Type: `multipart/form-data`, `application/x-www-form-urlencoded`

Parameters have same meaning as in case of [POST Workspace Layers](#post-workspace-layers).

Body parameters:
- *file*, file(s) or file name(s)
   - If provided, current layer vector data file will be deleted and replaced by this file. GeoServer feature types, DB table, and thumbnail will be deleted and created again using the new file.
   - one of following options is expected:
      - GeoJSON file
      - ShapeFile files (at least three files: .shp, .shx, .dbf)
      - file names, i.e. array of strings
   - if file names are provided, files must be uploaded subsequently using [POST Workspace Layer Chunk](#post-workspace-layer-chunk)
   - if published file has empty bounding box (i.e. no features), its bounding box on WMS/WFS endpoint is set to the whole World
   - if QML style is used (either directly within this request, or indirectly from previous state on server), it must list all attributes contained in given data file
- *title*
- *description*
- *crs*, string `EPSG:3857` or `EPSG:4326`
   - Taken into account only if `file` is provided.
- *style*, style file
   - SLD or QML style file (recognized by the root element of XML: `StyledLayerDescriptor` or `qgis`)
   - attribute names are [laundered](https://gdal.org/drivers/vector/pg.html#layer-creation-options) to be in line with DB attribute names
   - If provided, current layer thumbnail will be temporarily deleted and created again using the new style.
- *access_rights.read*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [read access](./security.md#publication-access-rights) to this publication
- *access_rights.write*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [write access](./security.md#publication-access-rights) to this publication
- ~~sld~~, SLD file
   - **deprecated parameter**
   - alias for *style* parameter
#### Response
Content-Type: `application/json`

JSON object, same as in case of [GET Workspace Layer](#get-workspace-layer), possibly extended with one extra property:
- *files_to_upload*: List of objects. It's present only if **file** parameter contained file names. See [POST Workspace Layers](#post-workspace-layers) response to find out more.

### DELETE Workspace Layer
Delete existing layer and all associated sources, including vector data file and DB table. It is possible to delete layer, whose publication process is still running. In such case, the publication process is aborted safely.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON object representing deleted layer:
- **name**: String. Former name of the layer.
- **uuid**: String. Former UUID of the layer.
- **url**: String. Former URL of the layer. It points to [GET Workspace Layer](#get-workspace-layer).


## Workspace Layer Thumbnail
### URL
`/rest/workspaces/<workspace_name>/layers/<layername>/thumbnail`
### GET Workspace Layer Thumbnail
Get thumbnail of the layer in PNG format, 300x300 px, transparent background.

#### Request
No action parameters.
#### Response
Content-Type: `image/png`

PNG image.


## Workspace Layer Style
### URL
`/rest/workspaces/<workspace_name>/layers/<layername>/style`
### GET Workspace Layer Style
Get default style of the layer in XML format. Request is redirected to GeoServer [/rest/workspaces/{workspace}/styles/{style}](https://docs.geoserver.org/latest/en/api/#1.0.0/styles.yaml) for layers with SLD style. For layers with QML style, response is created in Layman. Anybody can call GET, nobody can call any other method. 

#### Request
No action parameters.
#### Response
Content-Type:
  - `application/vnd.ogc.sld+xml` or `application/vnd.ogc.se+xml` for SLD
  - `application/x-qgis-layer-settings` for QML


## Workspace Layer Chunk
Layer Chunk endpoint enables to upload layer data files asynchronously by splitting them into small parts called *chunks* that are uploaded independently. The endpoint is expected to be operated using [Resumable.js](http://www.resumablejs.com/) library. Resumable.js can split and upload files by chunks using [HTML File API](https://developer.mozilla.org/en-US/docs/Web/API/File), widely [supported by major browsers](https://caniuse.com/#feat=fileapi).

Check [Asynchronous file upload](async-file-upload.md) example. 

The endpoint is activated after [POST Workspace Layers](#post-workspace-layers) or [PATCH Workspace Layer](#patch-workspace-layer) request if and only if the **file** parameter contained file name(s). The endpoint is active till first of the following happens:
- all file chunks are uploaded
- no chunk is uploaded within [UPLOAD_MAX_INACTIVITY_TIME](../src/layman_settings.py)
- layer is deleted

### URL
`/rest/<workspace_name>/layers/<layername>/chunk`
### GET Workspace Layer Chunk
Test if file chunk is already uploaded on the server.

#### Request
Query parameters:
- **layman_original_parameter**, name of parameter of preceding request ([POST Workspace Layers](#post-workspace-layers) or [PATCH Workspace Layer](#patch-workspace-layer)) that contained the file name
- **resumableFilename**, name of file whose chunk is requested
- **resumableChunkNumber**, serial number of requested chunk

#### Response
Content-Type: `application/json`

HTTP status code 200 if chunk is already uploaded on the server, otherwise 404.

### POST Workspace Layer Chunk
Upload file chunk to the server.

#### Request
Content-Type: `multipart/form-data`

Body parameters:
- **file**, uploaded chunk
- **resumableChunkNumber**, serial number of uploaded chunk
- **resumableFilename**, name of file whose chunk is uploaded
- **layman_original_parameter**, name of parameter of preceding request ([POST Workspace Layers](#post-workspace-layers) or [PATCH Workspace Layer](#patch-workspace-layer)) that contained the file name
- **resumableTotalChunks**, number of chunks the file is split to

#### Response
Content-Type: `application/json`

HTTP status code 200 if chunk was successfully saved.


### GET Workspace Layer Metadata Comparison
Get comparison of metadata properties among Layman, CSW, WMS and WFS.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON object with one attribute:
- **metadata_sources**: Dictionary of objects. Key is ID of metadata source valid for this JSON only (not persistent in time!). Value is object with following attributes:
  - **url**: String. URL of the metadata source ([GET Workspace Layer](#get-workspace-layer), CSW record, WMS Capabilities, or WFS Capabitilities).
- **metadata_properties**: Dictionary of objects. Key is name of [metadata property](./metadata.md) (e.g. `reference_system`). Value is object with following attributes:
  - **values**: Dictionary of objects. Key is ID of metadata source corresponding with `metadata_sources` attribute. Value is any valid JSON (null, number, string, boolean, list, or object) representing value of [metadata property](./metadata.md) (e.g. `[3857, 4326]`). Null means the value is not set.
  - **equal**: Boolean. True if all values are considered equal, false otherwise.
  - **equal_or_null**: Boolean. True if all values are considered equal or null, false otherwise.


## Maps
### URL
`/rest/maps`

### GET Maps
Get list of published maps (map compositions).

#### Request
Query parameters:
- *full_text_filter*: String. List of words separated by space. Only maps with at least one of them in title will be returned. Search is case-insensitive, unaccent and did lemmatization for English. By default, maps are ordered by search rank in response if this filter is used.
- *bbox_filter*: String. Bounding box in EPSG:3857 defined by four comma-separated coordinates `minx,miny,maxx,maxy`. Only maps whose bounding box intersects with given bounding box will be returned.
- *order_by*: String. Can be one of these values:
  - `full_text` Publications will be ordered by results of full-text search. Can be used only in combination with *full_text_filter*.
  - `title` Publications will be ordered lexicographically by title value.
  - `last_change` Publications will be ordered by time of last change. Recently updated publications will be first.

#### Response
Content-Type: `application/json`

JSON array of objects representing available maps with following structure:
- **workspace**: String. Name of the map's workspace.
- **name**: String. Name of the map.
- **title**: String. Title of the map.
- **uuid**: String. UUID of the map.
- **url**: String. URL of the map. It points to [GET Workspace Map](#get-workspace-map).
- **updated_at**: String. Date and time of last POST/PATCH of the publication. Format is [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601), more specifically `YYYY-MM-DDThh:mm:ss.sss±hh:mm`, always in UTC. Sample value: `"2021-03-18T09:29:53.769233+00:00"`
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).
- **bounding_box**: List of 4 floats. Bounding box coordinates [minx, miny, maxx, maxy] in EPSG:3857.


## Workspace Maps
### URL
`/rest/workspaces/<workspace_name>/maps`

### GET Workspace Maps
Get list of published maps (map compositions).

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON array of objects representing available maps with following structure:
- **workspace**: String. Name of the map's workspace.
- **name**: String. Name of the map.
- **title**: String. Title of the map.
- **uuid**: String. UUID of the map.
- **url**: String. URL of the map. It points to [GET Workspace Map](#get-workspace-map).
- **updated_at**: String. Date and time of last POST/PATCH of the publication. Format is [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601), more specifically `YYYY-MM-DDThh:mm:ss.sss±hh:mm`, always in UTC. Sample value: `"2021-03-18T09:29:53.769233+00:00"`
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).
- **bounding_box**: List of 4 floats. Bounding box coordinates [minx, miny, maxx, maxy] in EPSG:3857.

### POST Workspace Maps
Publish new map composition. Accepts JSON valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema) used by [Hslayers-ng](https://github.com/hslayers/hslayers-ng).

Processing chain consists of few steps:
- validate JSON file against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema)
- save file to workspace directory
- if needed, update some JSON attributes (`name`, `title`, or `abstract`)
- generate thumbnail image
- publish metadata record to Micka (it's public if and only if read access is set to EVERYONE)
- save basic information (name, title, access_rights) into PostgreSQL

If workspace directory does not exist yet, it is created on demand.

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
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [read access](./security.md#publication-access-rights) to this publication
   - default value is current authenticated user, or EVERYONE if published by anonymous
- *access_rights.write*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [write access](./security.md#publication-access-rights) to this publication
   - default value is current authenticated user, or EVERYONE if published by anonymous

#### Response
Content-Type: `application/json`

JSON array of objects representing posted maps with following structure:
- **name**: String. Name of the map.
- **uuid**: String. UUID of the map.
- **url**: String. URL of the map. It points to [GET Workspace Map](#get-workspace-map).

### DELETE Workspace Maps
Delete existing maps and all associated sources, including map-composition JSON file and map thumbnail for all mapss in the workspace. Only maps on which user has [write access right](./security.md#access-to-multi-publication-endpoints) are deleted.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON array of objects representing deleted maps:
- **name**: String. Former name of the map.
- **title**: String. Former title of the map.
- **uuid**: String. Former UUID of the map.
- **url**: String. Former URL of the map. It points to [GET Workspace Map](#get-workspace-map).
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with former [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with former [write access](./security.md#Authorization).

## Workspace Map
### URL
`/rest/workspaces/<workspace_name>/maps/<mapname>`

#### Endpoint path parameters
- **mapname**
   - map name used for identification
   - it can be obtained from responses of [GET Workspace Maps](#get-workspace-maps), [POST Workspace Maps](#post-workspace-maps), and all responses of this endpoint

### GET Workspace Map
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
- **updated_at**: String. Date and time of last POST/PATCH of the publication. Format is [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601), more specifically `YYYY-MM-DDThh:mm:ss.sss±hh:mm`, always in UTC. Sample value: `"2021-03-18T09:29:53.769233+00:00"`
- **file**
  - *url*: String. URL of map-composition JSON file. It points to [GET Workspace Map File](#get-workspace-map-file).
  - *path*: String. Path to map-composition JSON file, relative to workspace directory.
  - *status*: Status information about availability of file. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **thumbnail**
  - *url*: String. URL of map thumbnail. It points to [GET Workspace Map Thumbnail](#get-workspace-map-thumbnail).
  - *status*: Status information about generating and availability of thumbnail. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- *metadata*
  - *identifier*: String. Identifier of metadata record in CSW instance.
  - *record_url*: String. URL of metadata record accessible by web browser, probably with some editing capabilities.
  - *csw_url*: String. URL of CSW endpoint. It points to CSW endpoint of Micka.
  - *comparison_url*: String. URL of [GET Workspace Map Metadata Comparison](#get-workspace-map-metadata-comparison).
  - *status*: Status information about metadata import and availability. See [GET Workspace Map](#get-workspace-map) 
  - *error*: If status is FAILURE, this may contain error object.
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).
- **bounding_box**: List of 4 floats. Bounding box coordinates [minx, miny, maxx, maxy] in EPSG:3857.

### PATCH Workspace Map
Update information about existing map. First, it deletes sources of the map, and then it publishes them again with new parameters. The processing chain is similar to [POST Workspace Maps](#post-workspace-maps).

#### Request
Content-Type: `multipart/form-data`, `application/x-www-form-urlencoded`

Parameters have same meaning as in case of [POST Workspace Maps](#post-workspace-maps).

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
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [read access](./security.md#publication-access-rights) to this publication
- *access_rights.write*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [write access](./security.md#publication-access-rights) to this publication

#### Response
Content-Type: `application/json`

JSON object, same as in case of [GET Workspace Map](#get-workspace-map).

### DELETE Workspace Map
Delete existing map and all associated sources, including map-composition JSON file and map thumbnail.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON object representing deleted map:
- **name**: String. Former name of the map.
- **uuid**: String. Former UUID of the map.
- **url**: String. Former URL of the map. It points to [GET Workspace Map](#get-workspace-map).


## Workspace Map File
### URL
`/rest/workspaces/<workspace_name>/maps/<mapname>/file`
### GET Workspace Map File
Get JSON file describing the map valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema).

Notice that some JSON properties are automatically updated by layman, so file obtained by this endpoint may be slightly different from file that was uploaded. Expected changes:
- **name** set to `<mapname>` in URL of this endpoint
- **title** obtained from [POST Workspace Maps](#post-workspace-maps) or [PATCH Workspace Map](#patch-workspace-map) as `title`
- **abstract** obtained from [POST Workspace Maps](#post-workspace-maps) or [PATCH Workspace Map](#patch-workspace-map) as `description`
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


## Workspace Map Thumbnail
### URL
`/rest/workspaces/<workspace_name>/maps/<mapname>/thumbnail`
### GET Workspace Map Thumbnail
Get thumbnail of the map in PNG format, 300x300 px, transparent background.

#### Request
No action parameters.
#### Response
Content-Type: `image/png`

PNG image.


### GET Workspace Map Metadata Comparison
Get comparison of metadata properties among Layman and CSW.

#### Request
No action parameters.

#### Response
Content-Type: `application/json`

JSON object with one attribute:
- **metadata_sources**: Dictionary of objects. Key is ID of metadata source valid for this JSON only (not persistent in time!). Value is object with following attributes:
  - **url**: String. URL of the metadata source ([GET Workspace Map](#get-workspace-map), [GET Workspace Map File](#get-workspace-map-file), or CSW record).
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
- *username*: String. [Username](models.md#username) the user reserved within Layman. If not set, it was not reserved yet. To be used as username in some REST API paths (i.e. `/rest/workspaces/<username>/...`)

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

## Version
### URL
`/rest/about/version`

### GET Version
Get information about current application version.

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON object representing current application version:
- **about**
  - **applications**: Object with information about each application. 
    - **layman**:
      - **version**: String. The current version of Layman app. In [semantic versioning](https://semver.org/) format `X.Y.Z`, with suffix `-dev` for the development version.
      - **release-timestamp**: Datetime. Date and time of the release. For development version, date and time of the last public release.
    - **layman-test-client**:
      - **version**: String. The current version of installed Layman test client. In [semantic versioning](https://semver.org/) format `X.Y.Z`, or commit hash for development version.
  - **data** 
    - **layman**:
      - **last-schema-migration**: String. Identifier of the last successful schema migration in format 'X.Y.Z-m'.
      - **last-data-migration**: String. Identifier of the last successful data migration in format 'X.Y.Z-m'.
      - **last-migration**:
        - **deprecated parameter**
        - alias for *last-schema-migration* parameter
