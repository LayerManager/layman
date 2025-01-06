# REST API

## Overview
|Endpoint|URL|GET|POST|PATCH|DELETE|
|---|---|---|---|---|---|
|Publications|`/rest/publications`|[GET](#get-publications)| x | x | x |
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
|Roles|`/rest/roles`|[GET](#get-roles)| x | x | x |
|Version|`/rest/about/version`|[GET](#get-version)| x | x | x |

#### REST path parameters
- **workspace_name**, string `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`
   - string identifying [workspace](models.md#workspace)
  
**_NOTE:_** Before version 1.10.0, workspace-related endpoints did not include `/workspaces` in their path. These old endpoints are still functional, but deprecated. More specifically, they return HTTP header **Deprecation**. If you get such header in response, rewrite your client to use new endpoint path. Old endpoints will stop working in the next major release.

## Publications
### URL
`/rest/publications`

### GET Publications
Get list of published publications, i.e. layers and maps.

#### Request
Query parameters:
- *full_text_filter*: String. Only publications satisfying any of following conditions are returned:
  - Any word from input string appears in title. Search is case-insensitive, unaccent and does lemmatization for English.
  - Input string appears as substring of title. Search is case-insensitive and unaccent.
- *bbox_filter*: String. Bounding box defined by four comma-separated coordinates `minx,miny,maxx,maxy`. Only publications whose bounding box intersects with given bounding box will be returned.
- *bbox_filter_crs*: String. CRS of *bbox_filter*, default value is `EPSG:3857`, has to be one of [LAYMAN_OUTPUT_SRS_LIST](env-settings.md#LAYMAN_OUTPUT_SRS_LIST).
- *order_by*: String. Can be one of these values:
  - `full_text` Publications will be ordered by results of full-text search. Can be used only in combination with *full_text_filter*.
  - `title` Publications will be ordered lexicographically by title value.
  - `last_change` Publications will be ordered by time of last change. Recently updated publications will be first.
  - `bbox` Publications will be ordered by similarity of bounding box with bounding box passed in *ordering_bbox* or *bbox_filter*. Can be used only in combination with  *ordering_bbox* or *bbox_filter*.
  
  If *full_text_filter* is set, default value is `full_text`; if *bbox_filter* is set, default value is `bbox`; otherwise default value is empty string, i.e. no ordering is guaranteed.
- *ordering_bbox*: String. Bounding box defined by four comma-separated coordinates `minx,miny,maxx,maxy`. The bounding box will be used for ordering. Can be used only if *order_by* is set to `bbox` (by default or explicitly). If *order_by* is set to `bbox`, default value of *ordering_bbox* is the value of *bbox_filter*.
- *ordering_bbox_crs*: String. CRS of *ordering_bbox*, default value is *bbox_filter_crs* if defined otherwise `EPSG:3857`, has to be one of [LAYMAN_OUTPUT_SRS_LIST](env-settings.md#LAYMAN_OUTPUT_SRS_LIST).
- *limit*: Non-negative Integer. No more publications than this number will be returned. But possibly less, if the query itself yields fewer publications.
- *offset*: Non-negative Integer. Says to skip that many publications before beginning to return publications.

#### Response
Content-Type: `application/json`

JSON array of objects representing available layers and maps with following structure:
- **workspace**: String. Name of the layer's workspace.
- **publication_type**: String. Value `layer` for layers and `map` for maps.
- **name**: String. Name of the layer.
- **title**: String. Title of the layer.
- **uuid**: String. UUID of the layer.
- **url**: String. URL of the layer. It points to [GET Workspace Layer](#get-workspace-layer).
- **updated_at**: String. Date and time of last POST/PATCH of the layer. Format is [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601), more specifically `YYYY-MM-DDThh:mm:ss.sss±hh:mm`, always in UTC. Sample value: `"2021-03-18T09:29:53.769233+00:00"`
- **access_rights**:
  - **read**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [read access](./security.md#Authorization).
  - **write**: Array of strings. Names of [users](./models.md#user) and [roles](./models.md#role) with [write access](./security.md#Authorization).
- **bounding_box**: List of 4 floats. Bounding box coordinates [minx, miny, maxx, maxy] in EPSG:3857.
- **native_crs**: Code of native CRS in form "EPSG:&lt;code&gt;", e.g. "EPSG:4326".
- **native_bounding_box**: List of 4 floats and one string. Bounding box coordinates [minx, miny, maxx, maxy] in native CRS.
- *geodata_type*: String. Available only for layers. Either `vector`, `raster`, or `unknown`. Value `unknown` is used if input files are zipped and still being uploaded.
- *wfs_wms_status*: String. Available only for layers. Status of layer availability in WMS (and WFS in case of vector data) endpoints. Either `AVAILABLE`, `PREPARING`, or `NOT_AVAILABLE`.

Headers:
- **X-Total-Count**: Total number of layers available from the request, taking into account all filtering parameters except `limit` and `offset`. Example `"247"`.
- **Content-Range**: Indicates where in a full list of layers a partial response belongs. Syntax of value is `<units> <range_start>-<range_end>/<size>`. Value of `units` is always `items`. Value of `range_start` is one-based index of the first layer within the full list, or zero if no values are returned. Value of `range_end` is one-based index of the last layer within the full list, or zero if no values are returned. Example: `items 1-20/247`.

## Layers
### URL
`/rest/layers`

### GET Layers
Get list of published layers.

Have the same request parameters and response structure and headers as [GET Publications](#get-publications), except only layers are returned.

## Workspace Layers
### URL
`/rest/workspaces/<workspace_name>/layers`

### GET Workspace Layers
Get list of published layers.

Have the same request parameters and response structure and headers as [GET Layers](#get-layers).

### POST Workspace Layers
Publish vector or raster data as new WMS layer, in case of vector data also new WFS feature type.

Processing chain consists of few steps:
- save files (if sent) to workspace directory within Layman data directory
- save basic information (name, title, access_rights) into PostgreSQL
- for vector layers import vector file (if sent) to PostgreSQL database as new table into workspace schema
  - files with invalid byte sequence are first converted to GeoJSON, then cleaned with iconv, and finally imported to database.
- for raster layers normalize and compress raster file to GeoTIFF with overviews (pyramids); NoData values are normalized as transparent
- save bounding box into PostgreSQL
- for vector layers publish the vector table as new layer (feature type) within appropriate WFS workspaces of GeoServer
- for vector layers
  - for layers with SLD or none style:
    - publish the table as new layer (feature type) within appropriate WMS workspaces of GeoServer
  - for layers with QML style:
    - create QGS file on QGIS server filesystem with appropriate style
    - publish the layer on GeoServer through WMS cascade from QGIS server
- for raster layers publish normalized GeoTIFF as new layer (coverage) on GeoServer WMS workspace
- generate thumbnail image
- publish metadata record to Micka (it's public if and only if read access is set to EVERYONE)
- update thumbnail of each [map](models.md#map) that points to this layer

If workspace directory, database schema, GeoServer's workspaces, or GeoServer's datastores does not exist yet, it is created on demand.

Response to this request may be returned sooner than the processing chain is finished to enable [asynchronous processing](async-tasks.md). Status of processing chain can be seen using [GET Workspace Layer](#get-workspace-layer) and **layman_metadata.publication_status** property or **status** properties of layer sources (wms, wfs, thumbnail, db_table, file, style, metadata) for higher granularity.

It is possible to upload data files asynchronously, which is suitable for large files. This can be done in three steps:
1. Send POST Workspace Layers request with **file** parameter filled by file names that you want to upload
2. Read set of files accepted to upload from POST Workspace Layers response, **files_to_upload** property. The set of accepted files will be either equal to or subset of file names sent in **file** parameter.
3. Send [POST Workspace Layer Chunk](#post-workspace-layer-chunk) requests using Resumable.js to upload files.

Check [Asynchronous file upload](async-file-upload.md) example.

#### Request
Content-Type: `multipart/form-data`, `application/x-www-form-urlencoded`

Body parameters:
- *file*, file(s) or file name(s)
   - exactly one of `file` or `external_table_uri` must be set
   - one of following options is expected:
      - GeoJSON file
      - ShapeFile files (at least three files: .shp, .shx, .dbf)
      - GeoTIFF (.tif or .tiff, with or without .tfw, .tifw, .tiffw or .wld)
      - JPEG 2000 (.jp2, with or without .j2w, jp2w or .wld)
      - PNG (.png, with .png.aux.xml, .pgw, .pngw or .wld)
      - JPEG (.jpg, .jpeg, with .jpg.aux.xml, .jgw, .jpgw, .jpegw or .wld)
      - any of above types in single ZIP file (.zip)
      - file names, i.e. array of strings
   - it is allowed to publish time-series layer by setting time_regex parameter and sending one or more main raster files (compressed in one archive or uncompressed) with the same extension, color interpretation, pixel size, nodata value, mask flags, and data type name. Filename can be at most 210 characters long. Supported characters are 26 Latin letters `a-zA-Z` (with or without diacritics), numbers, underscores, dashes, dots, and spaces. Other Latin characters (e.g. ligatures `ß` or `Æ`) and other than Latin scripts (e.g. Cyrillic or Chinese) are not supported. Files are stored and published with slugified filenames (diacritic is removed from letters, and space ` ` is converted to underscore `_`).
   - if file names are provided, files must be uploaded subsequently using [POST Workspace Layer Chunk](#post-workspace-layer-chunk)
   - in case of raster data input, following input combinations of bands and color interpretations are supported:
      - 1 band: Gray
      - 1 band: Palette
      - 2 bands: Gray, Alpha
         - Opacity of WMS layer derived from Alpha band will be simplified to either fully transparent, or fully opaque (0 cells in Alpha convert to fully transparent, other cells convert to fully opaque).
      - 3 bands: Red, Green, Blue
      - 4 bands: Red, Green, Blue, Alpha
   - if published file has empty bounding box (i.e. no features), its bounding box on WMS/WFS endpoint is set to the whole World
   - attribute names are [laundered](https://gdal.org/en/stable/drivers/vector/pg.html#layer-creation-options) to be safely stored in DB
   - if QML style is used in this request, it must list all attributes contained in given data file
- *external_table_uri*, string
   - exactly one of `file` or `external_table_uri` must be set
   - [connection URI](https://www.postgresql.org/docs/15/libpq-connect.html#id-1.7.3.8.3.6) is required, usual format is `postgresql://<username>:<password>@<host>:<port>/<dbname>?schema=<schema_name>&table=<table_name>&geo_column=<geo_column_name>`
     - `host` part and query parameters `schema` and `table` are mandatory
     - URI scheme is required to be `postgresql`
     - `host.docker.internal` can be used to reach `localhost` of host server
   - if `geo_column` is not specified, first geometry column of the table by alphabetic order is used
   - published table is required to have one-column primary key
   - names of schema, table and all columns of the table are required to match regular expression `^[a-zA-Z_][a-zA-Z_0-9]*$`
   - DB user must have at least following privileges:
     - `SELECT` on the table referenced in URI
       - also `INSERT`, `UPDATE`, and/or `DELETE` if you want the layer to be editable using [WFS-T](endpoints.md#web-feature-service)
     - `SELECT` on tables in [information_schema](https://www.postgresql.org/docs/current/information-schema.html)
     - `SELECT` on [system catalogs](https://www.postgresql.org/docs/15/catalogs-overview.html)
     - `SELECT` on `public.geometry_columns` schema
     - `EXECUTE` or `USAGE` on PostGIS functions and types
   - the parameter is not meant to publish tables from Layman's database [LAYMAN_PG_DBNAME](env-settings.md#layman_pg_dbname); such usage can easily damage Layman's database, so do it only at **your own risk!**
- *name*, string
   - computer-friendly identifier of the layer
   - must be unique among all layers of one workspace
   - by default, it is file name without extension
     - for layers with more than one main file, it is the first one in alphabetic order
     - for layers published from external table, it is table name
   - maximal length is 210 characters
   - will be automatically adjusted using `to_safe_layer_name` function
- *title*, string `.+`
   - human readable name of the layer
   - by default it is layer name
- *description*
   - by default it is empty string
- *crs*, string, e.g. `EPSG:3857`, supported EPSG codes are defined by [LAYMAN_INPUT_SRS_LIST](./env-settings.md#LAYMAN_INPUT_SRS_LIST)
   - supported only for layers with file source
   - CRS of the file
   - by default it is read/guessed from input file
- *style*, style file
   - by default either default SLD style of GeoServer, or customized SLD created by Layman is used
     - default customized SLD file is created only for grayscale raster input files with or without alpha band to stabilize contrast in WMS; [ColorMap with type `ramp`](https://docs.geoserver.org/2.21.x/en/user/styling/sld/reference/rastersymbolizer.html#colormap) is used
   - SLD or QML style file (recognized by the root element of XML: `StyledLayerDescriptor` or `qgis`)
     - QML style for raster data file is not supported
     - It's possible to encode also external images in QML styles and use them in the style. To do so, each image needs to be encoded in Base64 encoding inside QML file. You can achieve it by selecting "Embed File" option in QGIS Layer Symbology window, see e.g. QGIS issues [2815](https://github.com/qgis/QGIS-Documentation/issues/2815) or [4563](https://github.com/qgis/QGIS-Documentation/pull/4563).
   - uploading of additional style files, e.g. point-symbol images or fonts is not supported
   - attribute names are [laundered](https://gdal.org/en/stable/drivers/vector/pg.html#layer-creation-options) to be in line with DB attribute names
- *access_rights.read*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [read access](./security.md#publication-access-rights) to this publication
   - default value is current authenticated user, or EVERYONE if published by anonymous
- *access_rights.write*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [write access](./security.md#publication-access-rights) to this publication
   - default value is current authenticated user, or EVERYONE if published by anonymous
- ~~sld~~, SLD file
   - **deprecated parameter**
   - alias for *style* parameter
- *overview_resampling*, string
   - supported only for raster layers
   - method used by [`gdaladdo`](https://gdal.org/en/stable/programs/gdaladdo.html#cmdoption-gdaladdo-r) for overview resampling when normalizing raster layer
   - by default Layman will guess overview resampling method from input file metadata
   - supported values are: `nearest`, `average`, `rms`, `bilinear`, `gauss`, `cubic`, `cubicspline`, `lanczos`, `average_magphase` and `mode`
- *time_regex*, string, e.g. `[0-9]{8}T[0-9]{6}Z`
  - regular expression pattern used for extracting the time information from [timeseries](models.md#timeseries) raster file names. The pattern
    - either has no matching group and matches ISO 8601 [year](https://en.wikipedia.org/wiki/ISO_8601#Years), [date](https://en.wikipedia.org/wiki/ISO_8601#Calendar_dates), or [datetime](https://en.wikipedia.org/wiki/ISO_8601#Combined_date_and_time_representations) patterns, e.g. `[0-9]{8}` or `[0-9]{8}T[0-9]{6}Z`
    - or has one or more matching groups that concatenated together matches ISO 8601 year, date, or datetime patterns, e.g. `^some_prefix_([0-9]{8})_some_postfix.*$` or , e.g. `some_prefix_([0-9]{8})_some_separator_(T[0-9]{6}Z)_some_postfix`
  - although time pattern is accepted in time_regex, the temporal part is later cut off, so the smallest recognizable temporal unit is one day (see [#875](https://github.com/LayerManager/layman/issues/875))
  - latin diacritic is removed from the regex and spaces are replaced with underscores to be consistent with slugifying of timeseries filenames
  - error is raised if any of main data file names do not match *time_regex* value
- *time_regex_format*, string, e.g. yyyyddMM
  - description of `time_regex` result format as [java SimpleDateFormat](https://docs.oracle.com/javase/7/docs/api/java/text/SimpleDateFormat.html), [GeoServer examples](https://docs.geoserver.geo-solutions.it/edu/en/multidim/imagemosaic/mosaic_indexer.html#format)
  - supported only in combination with `time_regex`

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
Delete existing layers and all associated sources except external DB tables published using `external_table_uri`. So it deletes e.g. data file, vector internal DB table or normalized raster files for all layers in the workspace. The currently running [asynchronous tasks](async-tasks.md) of affected layers are aborted. Only layers on which user has [write access right](./security.md#access-to-multi-publication-endpoints) are deleted.

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
- **layman_metadata**
  - **publication_status**: String. Can be one of these values:
    - **COMPLETE**: the layer is fully updated and response is final and up-to-date.
    - **INCOMPLETE**: some step of updating process failed, so the response is final, but missing some information.
    - **UPDATING**: some process is currently updating the layer (i.e. post, patch, wfs-t) so the response may change.
- **url**: String. URL pointing to this endpoint.
- **title**: String.
- **description**: String.
- **updated_at**: String. Date and time of last POST/PATCH of the publication. Format is [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601), more specifically `YYYY-MM-DDThh:mm:ss.sss±hh:mm`, always in UTC. Sample value: `"2021-03-18T09:29:53.769233+00:00"`
- **wms**
  - *url*: String. URL of WMS endpoint. It points to WMS endpoint of appropriate GeoServer workspace.
  - *time*, available only for time-series layers
    - **units**: String. Code of time format. Always `ISO8601`.
    - **values**: List of strings. Time instants available for layer written in ISO 8601 format.
      - time part of the value is always `00:00:00.000Z` (see [#875](https://github.com/LayerManager/layman/issues/875))
    - **default**: Time. Default time instant.
      - time part of the value is always `00:00:00Z` (see [#875](https://github.com/LayerManager/layman/issues/875))
    - **regex**: Slugified regular expression used to extract time instants from file names. Originally sent in `time_regex` parameter.
    - **regex_format**: Slugified format of `regex` result date and time. Originally sent in `time_regex_format` parameter.
  - *status*: Status information about GeoServer import and availability of WMS layer. No status object means the source is available. Usual state values are
    - PENDING: publishing of this source is queued, but it did not start yet
    - STARTED: publishing of this source is in process
    - FAILURE: publishing process failed
    - NOT_AVAILABLE: source is not available, e.g. because publishing process failed
  - *error*: If status is FAILURE, this may contain error object.
- *wfs*, available only for vector layers
  - *url*: String. URL of WFS endpoint. It points to WFS endpoint of appropriate GeoServer workspace.
  - *status*: Status information about GeoServer import and availability of WFS feature type. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **thumbnail**
  - *url*: String. URL of layer thumbnail. It points to [GET Workspace Layer Thumbnail](#get-workspace-layer-thumbnail).
  - *status*: Status information about generating and availability of thumbnail. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **file**
  - *paths*: List of strings. Paths to all main input data files. Path is relative to workspace directory.  
  If data file was sent in ZIP archive to the server, path includes also path to the main file inside ZIP file. E.g. `layers/zipped_shapefile/input_file/zipped_shapefile.zip/layer_main_file.shp`
  - *~~path~~*:
    - **Deprecated**
    - Replaced by *paths*, which contains list of all data files.
    - String. Path to input data file. Path is relative to workspace directory.  
    If data file was sent in ZIP archive to the server, path includes also path to the main file inside ZIP file. E.g. `layers/zipped_shapefile/input_file/zipped_shapefile.zip/layer_main_file.shp`
  - *status*: Status information about saving and availability of files. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- *db*, available only for vector layers
  - *schema*: String. DB schema name within PostgreSQL database.
  - *table*: String. DB table name within PostgreSQL schema. This table is used as GeoServer source of layer.
  - *geo_column*: String. Geometry column of the table used by GeoServer.
  - *external_uri*: String. Available only for layers published from external table. Connection string to external table without password.
  - *status*: Status information about DB import and availability of the table. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- *~~db_table~~*: **Deprecated**. Replaced by **db**.
  - available only for vector layers
  - *~~name~~*: Replaced by db.table.
  - *~~status~~*: Replaced by db.status.
  - *~~error~~*: Replaced by db.error.
- **style**
  - *url*: String. URL of layer default style. It points to [GET Workspace Layer Style](#get-workspace-layer-style).
  - *type*: String. Type of used style. Either 'sld' or 'qml'.
  - *status*: Status information about publishing style. See [GET Workspace Layer](#get-workspace-layer) **wms** property for meaning.
  - *error*: If status is FAILURE, this may contain error object.
- **original_data_source**: String. Either `file` if layer was published from file, or `database_table` if layer was published from external database table 
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
- **native_crs**: Code of native CRS in form "EPSG:&lt;code&gt;", e.g. "EPSG:4326". Native CRS is CRS of the input data file.
- **native_bounding_box**: List of 4 floats. Bounding box coordinates [minx, miny, maxx, maxy] in native CRS.
- *image_mosaic*: Boolean. True for raster layers using `image_mosaic` plugin in GeoServer, so far only [timeseries](models.md#timeseries) layers. Available only for raster layer
- **geodata_type**: String. Either `vector`, `raster`, or `unknown`. Value `unknown` is used if input files are zipped and still being uploaded.

### PATCH Workspace Layer
Update information about existing layer. First, it deletes sources of the layer (except external DB table published using `external_table_uri`), and then it publishes them again with new parameters. The processing chain is similar to [POST Workspace Layers](#post-workspace-layers).

Response to this request may be returned sooner than the processing chain is finished to enable [asynchronous processing](async-tasks.md).

It is possible to upload data files asynchronously, which is suitable for large files. See [POST Workspace Layers](#post-workspace-layers).

Calling concurrent PATCH requests is not supported, as well as calling PATCH when [POST/PATCH async chain](async-tasks.md) is still running, is not allowed. In such cases, error is returned.

Calling PATCH request when [WFS-T async chain](async-tasks.md) is still running causes abortion of WFS-T async chain and ensures another run of WFS-T async chain after PATCH async chain is finished.

#### Request
Content-Type: `multipart/form-data`, `application/x-www-form-urlencoded`

Parameters have same meaning as in case of [POST Workspace Layers](#post-workspace-layers).

Body parameters:
- *file*, file(s) or file name(s)
   - If provided, current data file will be deleted and replaced by this file. GeoServer feature types, DB table, normalized raster file, and thumbnail will be deleted and created again using the new file.
   - same file types as in [POST Workspace Layers](#post-workspace-layers) are expected
   - only one of `file` or `external_table_uri` can be set
   - if file names are provided, files must be uploaded subsequently using [POST Workspace Layer Chunk](#post-workspace-layer-chunk)
   - if published file has empty bounding box (i.e. no features), its bounding box on WMS/WFS endpoint is set to the whole World
   - if QML style is used (either directly within this request, or indirectly from previous state on server), it must list all attributes contained in given data file
   - it is allowed to publish time-series layer - see [POST Workspace Layers](#post-workspace-layers)
- *external_table_uri*, string
   - only one of `file` or `external_table_uri` can be set
   - [connection URI](https://www.postgresql.org/docs/15/libpq-connect.html#id-1.7.3.8.3.6) is required, usual format is `postgresql://<username>:<password>@<host>:<port>/<dbname>?schema=<schema_name>&table=<table_name>&geo_column=<geo_column_name>`
     - `host` part and query parameters `schema` and `table` are mandatory
     - URI scheme is required to be `postgresql`
   - if `geo_column` is not specified, first geometry column of the table by alphabetic order is used
   - published table is required to have one-column primary key
   - names of schema, table and all columns of the table are required to match regular expression `^[a-zA-Z_][a-zA-Z_0-9]*$`
   - DB user must have at least following privileges:
     - `SELECT` on the table referenced in URI
       - also `INSERT`, `UPDATE`, and/or `DELETE` if you want the layer to be editable using [WFS-T](endpoints.md#web-feature-service)
     - `SELECT` on tables in [information_schema](https://www.postgresql.org/docs/current/information-schema.html)
     - `SELECT` on [system catalogs](https://www.postgresql.org/docs/15/catalogs-overview.html)
     - `SELECT` on `public.geometry_columns` schema
     - `EXECUTE` or `USAGE` on PostGIS functions and types
   - the parameter is not meant to publish tables from Layman's database [LAYMAN_PG_DBNAME](env-settings.md#layman_pg_dbname); such usage can easily damage Layman's database, so do it only at **your own risk!**
- *title*
- *description*
- *crs*, string, e.g. `EPSG:3857`, supported EPSG codes are defined by [LAYMAN_INPUT_SRS_LIST](./env-settings.md#LAYMAN_INPUT_SRS_LIST)
   - Supported only if `file` is provided.
- *style*, style file
   - SLD or QML style file (recognized by the root element of XML: `StyledLayerDescriptor` or `qgis`)
     - QML style for raster data file is not supported
     - It's possible to encode also external images in QML styles and use them in the style. See [POST Workspace Layers](#post-workspace-layers) body parameter *style* for details.
   - attribute names are [laundered](https://gdal.org/en/stable/drivers/vector/pg.html#layer-creation-options) to be in line with DB attribute names
   - If provided, current layer thumbnail will be temporarily deleted and created again using the new style.
- *access_rights.read*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [read access](./security.md#publication-access-rights) to this publication
- *access_rights.write*, string
   - comma-separated names of [users](./models.md#user) and [roles](./models.md#role) who will get [write access](./security.md#publication-access-rights) to this publication
- ~~sld~~, SLD file
   - **deprecated parameter**
   - alias for *style* parameter
- *overview_resampling*, string
   - supported only for raster layers
   - method used by [`gdaladdo`](https://gdal.org/en/stable/programs/gdaladdo.html#cmdoption-gdaladdo-r) for overview resampling when normalizing raster layer
   - by default Layman will guess overview resampling method from input file metadata
   - supported values are: `nearest`, `average`, `rms`, `bilinear`, `gauss`, `cubic`, `cubicspline`, `lanczos`, `average_magphase` and `mode`
   - can be used only together with `file` parameter, otherwise error is raised
- *time_regex*, string, e.g. `[0-9]{8}T[0-9]{6}Z`
  - supported only in combination with *file* parameter
  - see [POST Workspace Layers](#post-workspace-layers)
- *time_regex_format*, string, e.g. yyyyddMM
  - description of `time_regex` result format as [java SimpleDateFormat](https://docs.oracle.com/javase/7/docs/api/java/text/SimpleDateFormat.html), [GeoServer examples](https://docs.geoserver.geo-solutions.it/edu/en/multidim/imagemosaic/mosaic_indexer.html#format)
  - supported only in combination with `time_regex`

#### Response
Content-Type: `application/json`

JSON object, same as in case of [POST Workspace Layers](#post-workspace-layers).

### DELETE Workspace Layer
Delete existing layer and all associated sources except external DB table published using `external_table_uri`. So it deletes e.g. data file, vector internal DB table or normalized raster file. The currently running [asynchronous tasks](async-tasks.md) of affected layer are aborted.

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
Get thumbnail of the layer in PNG format, 300x300 px, transparent background, in native CRS.

#### Request
No action parameters.
#### Response
Content-Type: `image/png`

PNG image.


## Workspace Layer Style
### URL
`/rest/workspaces/<workspace_name>/layers/<layername>/style`
### GET Workspace Layer Style
Get default style of the layer in XML format. For layers with SLD style, request is redirected to GeoServer [/rest/workspaces/{workspace}/styles/{style}](https://docs.geoserver.org/2.21.x/en/api/#1.0.0/styles.yaml) and response is in version 1.0.0. For layers with QML style, response is created in Layman. Anybody can call GET, nobody can call any other method. 

#### Request
No action parameters.
#### Response
Content-Type:
  - `application/vnd.ogc.sld+xml` or `application/vnd.ogc.se+xml` for SLD
  - `application/x-qgis-layer-settings` for QML


## Workspace Layer Chunk
Layer Chunk endpoint enables to upload layer data files asynchronously by splitting them into small parts called *chunks* that are uploaded independently. The endpoint is expected to be operated using [Resumable.js](https://github.com/23/resumable.js/) library. Resumable.js can split and upload files by chunks using [HTML File API](https://developer.mozilla.org/en-US/docs/Web/API/File), widely supported by major browsers.

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

Have the same request parameters and response structure and headers as [GET Publications](#get-publications), except only maps are returned.

## Workspace Maps
### URL
`/rest/workspaces/<workspace_name>/maps`

### GET Workspace Maps
Get list of published maps (map compositions).

Have the same request parameters and response structure and headers as [GET Maps](#get-maps).

### POST Workspace Maps
Publish new map composition. Accepts JSON valid against [map-composition schema](https://github.com/hslayers/map-compositions) version 2 or 3 used by [Hslayers-ng](https://github.com/hslayers/hslayers-ng). Exact version of schema is defined by `describedBy` key of JSON data file.

Processing chain consists of few steps:
- validate JSON file against schema defined by `describedBy` key
- save file to workspace directory
- if needed, update some JSON attributes (`name`, `title`, or `abstract`)
- generate thumbnail image
- publish metadata record to Micka (it's public if and only if read access is set to EVERYONE)
- save basic information (name, title, access_rights) into PostgreSQL

Some of these steps run [asynchronously](async-tasks.md).

If workspace directory does not exist yet, it is created on demand.

Response to this request may be returned sooner than the processing chain is finished to enable asynchronous processing. Status of processing chain can be seen using [GET Workspace Map](#get-workspace-map) and **layman_metadata.publication_status** property or **status** properties of map sources (file, thumbnail, metadata) for higher granularity.

#### Request
Content-Type: `multipart/form-data`

Body parameters:
- **file**, JSON file
   - must be valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema)
   - layer is considered [internal](models.md#internal-map-layer) if
     - its URL points to the Layman instance (with or without client-proxy URL path prefix),
     - or its URL protocol and its URL host corresponds with [X-Forwarded headers](client-proxy.md#x-forwarded-http-headers) (with or without client-proxy URL path prefix)
- *name*, string
   - computer-friendly identifier of the map
   - must be unique among all maps of one workspace
   - by default, it is the first available of following options:
      - `name` attribute of JSON root object
      - `title` attribute of JSON root object
      - file name without extension
   - maximal length is 210 characters
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
Delete existing maps and all associated sources, including map-composition JSON file and map thumbnail for all maps in the workspace. The currently running [asynchronous tasks](async-tasks.md) of affected maps are aborted. Only maps on which user has [write access right](./security.md#access-to-multi-publication-endpoints) are deleted.

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
- **layman_metadata**
  - **publication_status**: String. Can be one of these values:
    - **COMPLETE**: map is fully updated and response is final and up-to-date.
    - **INCOMPLETE**: some step of updating process failed, so the response is final, but missing some information.
    - **UPDATING**: some process is currently updating the map (i.e. post, patch, wfs-t) so the response may change.
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
- **native_crs**: Code of native CRS in form "EPSG:&lt;code&gt;", e.g. "EPSG:4326". Native CRS is CRS of the input data file.
- **native_bounding_box**: List of 4 floats. Bounding box coordinates [minx, miny, maxx, maxy] in native CRS.

### PATCH Workspace Map
Update information about existing map. First, it deletes sources of the map, and then it publishes them again with new parameters. The processing chain is similar to [POST Workspace Maps](#post-workspace-maps), including [asynchronous tasks](async-tasks.md),

Calling concurrent PATCH requests is not supported, as well as calling PATCH when [POST/PATCH async chain](async-tasks.md) is still running, is not allowed. In such cases, error is returned.

Calling PATCH request when [WFS-T async chain](async-tasks.md) is still running causes abortion of WFS-T async chain and ensures another run of WFS-T async chain after PATCH async chain is finished.

#### Request
Content-Type: `multipart/form-data`, `application/x-www-form-urlencoded`

Parameters have same meaning as in case of [POST Workspace Maps](#post-workspace-maps).

Body parameters:
- *file*, JSON file
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

JSON object, same as in case of [POST Workspace Maps](#post-workspace-maps).

### DELETE Workspace Map
Delete existing map and all associated sources, including map-composition JSON file and map thumbnail. The currently running [asynchronous tasks](async-tasks.md) of affected map are aborted.

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
- [some layer URLs](client-proxy.md#x-forwarded-http-headers) according to X-Forwarded HTTP headers

#### Request
No action parameters.
#### Response
Content-Type: `application/json`

JSON file describing the map valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema).


## Workspace Map Thumbnail
### URL
`/rest/workspaces/<workspace_name>/maps/<mapname>/thumbnail`
### GET Workspace Map Thumbnail
Get thumbnail of the map in PNG format, 300x300 px, transparent background, in EPSG:3857.

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
- *username*: String. [Username](models.md#username) that should be reserved for current user (maximum length is 59 characters). Username can be reserved only once and cannot be changed. See URL parameter `adjust_username` for other details.

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

## Roles
### URL
`/rest/roles`

### GET Roles
Get list of [roles](models.md#role) available in [role service](security.md#role-service) in table `roles` except of [admin records](security.md#admin-role-service-records). Pseudo-role `EVERYONE` appear in the list too.  

#### Request.
No action parameters.

#### Response
Content-Type: `application/json`

JSON array of role names in alphabetical order, where each role name is a `string`.

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
      - **~~last-migration~~**:
        - **deprecated parameter**
        - alias for *last-schema-migration* parameter
