# Changelog

## v1.14.0
 {release_date}
### Upgrade requirements
- It's strongly recommended to backup data directories, especially `deps/postgresql/data`, because of database upgrade.
- After stopping layman and backing up data directories, you need to migrate PostgreSQL data directory from v10 to v13. We created script that automatically migrates two databases:
    - `gis` (Layman's database)
    - `hsrs_micka6` (Micka's database, only if exists)  
    If you use other databases in the postgres instance, their migration is up to you (you can inspire inside our script).

    **Migration script:**   
    ```
    # Enter your layman's root directory.
    cd /path/to/your/layman/instance
    
    # Run script for DB migration.
    # It's necessary to run this script from layman's root directory
    ./src/layman/upgrade/upgrade_v1_14_postgres.sh
    ```

    It may take some time to run this script and it will produce large temporary files (database dumps).
- Set environment variables
  - [LAYMAN_GS_NORMALIZED_RASTER_DIRECTORY](doc/env-settings.md#LAYMAN_GS_NORMALIZED_RASTER_DIRECTORY)=normalized_raster_data
  - [DEFAULT_CONNECTION_TIMEOUT](doc/env-settings.md#DEFAULT_CONNECTION_TIMEOUT)=10
- If you are running Layman with development settings, set environment variables
  - [LAYMAN_GS_NORMALIZED_RASTER_DIRECTORY](doc/env-settings.md#LAYMAN_GS_NORMALIZED_RASTER_DIRECTORY)=normalized_raster_data_dev
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.9.0`
    - If you are running Layman with development settings, run also `make client-build`.
### Migrations and checks
#### Schema migrations
#### Data migrations
### Changes
- [#167](https://github.com/LayerManager/layman/issues/167) Allow publishing also raster geospatial data from `GeoTiff` and `JPEG2000` formats using [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer). Following input combinations of bands and color interpretations are supported:
  - 1 band: Gray
  - 1 band: Palette
  - 2 bands: Gray, Alpha
  - 3 bands: Red, Green, Blue
  - 4 bands: Red, Green, Blue, Alpha
- [#167](https://github.com/LayerManager/layman/issues/167) Published raster files are normalized before registering to GeoServer. Normalization includes conversion to GeoTiff in EPSG:3857 with overviews (pyramids). NoData values are normalized as transparent only if Alpha band is not available and NoData is set for each band. Normalized rasters are stored in `normalized_raster_data` directory inside [LAYMAN_DATA_DIR](doc/env-settings.md#LAYMAN_DATA_DIR). Normalized GeoTiff is then published as new layer (coverage) on GeoServer. 
- [#167](https://github.com/LayerManager/layman/issues/167) Add `file_type` item to `file` item in [GET Workspace Layer](doc/rest.md#get-workspace-layer) response to distinguish raster and vector layer.
- [#167](https://github.com/LayerManager/layman/issues/167) Raster layers are not stored in DB table, for WFS and for WMS.
- [#167](https://github.com/LayerManager/layman/issues/167) [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) do not return items `wfs` and `db_table` for raster layers.
- [#167](https://github.com/LayerManager/layman/issues/167) Calling [WFS-T](doc/endpoints.md#web-feature-service) endpoint, causes [asynchronous tasks](doc/async-tasks.md) only for vector layers. 
- [#367](https://github.com/LayerManager/layman/issues/367) Upgrade gdal from 2.4 to 3.3. Use docker image from [osgeo/gdal@hub.docker.com](https://hub.docker.com/r/osgeo/gdal), source is located at [osgeo/gdal@github.com](https://github.com/OSGeo/gdal/tree/master/gdal/docker).
- [#367](https://github.com/LayerManager/layman/issues/367) Upgrade also
  - python from 3.6 to 3.8
  - flask from 1.1 to 2.0
  - werkzeug from 1 to 2
  - chromium from 77+ to 90+
  - chromedriver from 77+ to 90+
  - attrs from 20 to 21
  - click from 7 to 8
  - itsdangerous from 1 to 2
  - jinja2 from 2 to 3
  - markupsafe from 1 to 2
  - pytest-rerunfailures from 9 to 10
  - gunicorn from 19 to 20
- [#367](https://github.com/LayerManager/layman/issues/367) Limit bounding boxes of layers and maps to EPSG:3857 extent in all sources except DB table and filesystem.
- [#347](https://github.com/LayerManager/layman/issues/347) Upgrade PostgreSQL 10 to 13.3 and PostGIS 2.4 to 3.1. Use docker image from [layermanager/postgis@hub.docker.com](https://hub.docker.com/repository/docker/layermanager/postgis@github.com), source is located at [layermanager/docker-postgis@github.com](https://github.com/LayerManager/docker-postgis).
- [#347](https://github.com/LayerManager/layman/issues/347) When ordering publications by title, consider only letters, numbers, and spaces.
- [Map composition schema](https://github.com/LayerManager/layman/blob/master/src/layman/map/schema.draft-07.json) allows new properties `hs.format.externalWFS` and `workspace` ([#382](https://github.com/LayerManager/layman/pull/382)). The `style` property can be specified using a string in SLD format, URL to SLD file or JSON object ([#385](https://github.com/LayerManager/layman/pull/385)). Both was already introduced in v1.13.1.
- Errors `19`: 'Layer is already in process.' and `29`: 'Map is already in process.' are merged into `49`: 'Publication is already in process.'.
- Fix: Raise error when more than one main layer file is sent in [POST Workspace Layers](doc/rest.md#post-workspace-layers) or [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer).
- Fix [#408](https://github.com/LayerManager/layman/issues/408) Skip non WMS layers in thumbnail generation. Previously thumbnail generation failed.
- Fix [GET Workspace Layer](doc/rest.md#get-workspace-layer) documentation, where was incorrectly `style` item instead of `sld`.

## v1.13.2
 2021-06-25
### Changes
- Fix [#405](https://github.com/LayerManager/layman/issues/405). In some specific situations, [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [GET Workspace Map](doc/rest.md#get-workspace-map) returned PENDING state although asynchronous tasks were already finished. Also PATCH request to these publications was not possible. It's fixed now.

## v1.13.1
 2021-06-07
### Changes
- [Map composition schema](https://github.com/LayerManager/layman/blob/master/src/layman/map/schema.draft-07.json) allows new properties `hs.format.externalWFS` and `workspace` ([#382](https://github.com/LayerManager/layman/pull/382)). The `style` property can be specified using a string in SLD format, URL to SLD file or JSON object ([#385](https://github.com/LayerManager/layman/pull/385)).

## v1.13.0
 2021-05-26
### Upgrade requirements
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.8.0`
    - If you are running Layman with development settings, run also `make client-build`.
- If you are getting Layman using Git, run
```
git remote set-url origin https://github.com/layermanager/layman.git
```
- If you are running Layman with development settings, run  
```
make build-dev
make timgen-build
```
### Migrations and checks
#### Data migrations
- Rename filesystem directory containing workspaces from `users` to `workspaces`
### Changes
- Layman GitHub repository was moved from `https://github.com/jirik/layman` to https://github.com/LayerManager/layman. Thanks to GitHub redirect functionality, all former urls are deprecated and still work. The same change is done for Layman Test Client (https://github.com/LayerManager/layman-test-client)
- [#159](https://github.com/LayerManager/layman/issues/159) [WFS-T](doc/endpoints.md#web-feature-service) or [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) request causes
  - update of bounding box and thumbnail of each edited [layer](doc/models.md#layer)
     - bounding box is updated in DB, QGIS file, WMS/WFS capabilities, and CSW metadata record
     - thumbnail is updated in filesystem and it is accessible using [GET Workspace Layer Thumbnail](doc/rest.md#get-workspace-layer-thumbnail)
  - update of thumbnail of each [map](doc/models.md#map) that points to at least one edited layer (thumbnail is updated in filesystem and accessible using [GET Workspace Map Thumbnail](doc/rest.md#get-workspace-map-thumbnail))  
  These updates run in [asynchronous chain](doc/async-tasks.md). Documentation describes concurrency of WFS-T request and its asynchronous chains with another [WFS-T request](doc/endpoints.md#web-feature-service), [POST Workspace Layers](doc/rest.md#post-workspace-layers), [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer), [DELETE Workspace Layer](doc/rest.md#delete-workspace-layer), [DELETE Workspace Layers](doc/rest.md#delete-workspace-layers), [PATCH Workspace Map](doc/rest.md#patch-workspace-map), [DELETE Workspace Map](doc/rest.md#delete-workspace-map), and [DELETE Workspace Maps](doc/rest.md#delete-workspace-maps).
- [#159](https://github.com/LayerManager/layman/issues/159) Object `layman_metadata` was added to [GET Workspace Layer](doc/rest.md#get-workspace-layer), [GET Workspace Map](doc/rest.md#get-workspace-map), [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer), and [PATCH Workspace Map](doc/rest.md#patch-workspace-map) responses. Attribute `layman_metadata.publication_status` can be used for watching global state of publication (updating, complete, incomplete).
- [#331](https://github.com/LayerManager/layman/issues/331) Query parameter *full_text_filter* is also used for substring search in endpoints [GET Layers](doc/rest.md#get-layers), [GET Worksapce Layers](doc/rest.md#get-workspace-layers), [GET Maps](doc/rest.md#get-maps) and [GET Workspace Maps](doc/rest.md#get-workspace-maps).
- Filesystem directory containing workspaces was renamed from `users` to `workspaces`
- [#159](https://github.com/LayerManager/layman/issues/159) Bounding box is sent explicitly to GeoServer for every layer.
- [#72](https://github.com/LayerManager/layman/issues/72) Pipenv upgraded to v2020.11.15

## v1.12.0
 2021-04-21
### Upgrade requirements
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.7.0`
    - If you are running Layman with development settings, run also `make client-build`.
- Run [standalone upgrade](README.md#upgrade) before starting Layman.
### Migrations and checks
- Schema migrations (e.g. `ALTER TABLE ...` statements) and data migrations are split into separate lists. All schema migrations run before data migrations.
#### Schema migrations
- Adjust prime DB schema for two migration types, schema and data. Add new data type `enum_migration_type`, add new column `migration_type` to table `data_version` , insert second record to the table.
- [#257](https://github.com/LayerManager/layman/issues/257) Adjust prime DB schema for full-text filtering (install [unaccent](https://www.postgresql.org/docs/10/unaccent.html), create immutable `my_unaccent` function, index unaccented `title` column in `publications` table).
- [#257](https://github.com/LayerManager/layman/issues/257) Create new column `updated_at` in `publications` table.
- [#257](https://github.com/LayerManager/layman/issues/257) Create new column `bbox` in `publications` table.
#### Data migrations
- [#257](https://github.com/LayerManager/layman/issues/257) Fill column `updated_at` in `publications` table.
- [#302](https://github.com/LayerManager/layman/issues/302) Add URL parameter `LAYERS` to metadata properties [wms_url](doc/metadata.md#wms_url) and [wfs_url](doc/metadata.md#wfs_url) in existing metadata record of each layer. This non-standard parameter holds name of the layer at given WMS/WFS.
- [#257](https://github.com/LayerManager/layman/issues/257) Fill column `bbox` in `publications` table.
### Changes
- [#257](https://github.com/LayerManager/layman/issues/257) Endpoints [GET Layers](doc/rest.md#get-layers), [GET Worksapce Layers](doc/rest.md#get-workspace-layers), [GET Maps](doc/rest.md#get-maps) and [GET Workspace Maps](doc/rest.md#get-workspace-maps) can filter, order, and paginate results according to new query parameters. All request parameters, response structure and response headers are described in [GET Layers](doc/rest.md#get-layers) documentation.
- [#257](https://github.com/LayerManager/layman/issues/257) Responses of [GET Layers](doc/rest.md#get-layers), [GET Workspace Layers](doc/rest.md#get-workspace-layers), [GET Workspace Layer](doc/rest.md#get-workspace-layer), [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer), [GET Maps](doc/rest.md#get-maps), [GET Workspace Maps](doc/rest.md#get-workspace-maps), [GET Workspace Map](doc/rest.md#get-workspace-map), and [PATCH Workspace Map](doc/rest.md#patch-workspace-map) contains new attributes
   - `updated_at` with date and time of last PATCH/POST request to given publication
   - `bounding_box` with bounding box coordinates in EPSG:3857
- [#302](https://github.com/LayerManager/layman/issues/302) Metadata properties [wms_url](doc/metadata.md#wms_url) and [wfs_url](doc/metadata.md#wfs_url) contain new URL parameter `LAYERS` whose value is name of the layer. It's non-standard way how to store name of the layer at given WMS/WFS instance within metadata record.
- Migration version was split in [GET Version](doc/rest.md#get-version) to **last-schema-migration** and **last-data-migration**. Original **last-migration** stays as deprecated alias to **last-schema-migration**.

## v1.11.0
 2021-03-16
### Upgrade requirements
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.6.1`
    - If you are running Layman with development settings, run also `make client-build`.
### Changes
- [#273](https://github.com/LayerManager/layman/issues/273) New endpoints [GET Layers](doc/rest.md#get-layers) and [GET Layers](doc/rest.md#get-maps) to query publications in all [workspaces](doc/models.md#workspace).
- [#273](https://github.com/LayerManager/layman/issues/273) All Layer(s) and Map(s) endpoints with `<workspace_name>` in their URL were renamed to 'Workspace Layer...' and 'Workspace Map' in the documentation.
- [#273](https://github.com/LayerManager/layman/issues/273)  Item **workspace** was added to response of [GET Workspace Layers](doc/rest.md#get-workspace-layers) and [GET Workspace Maps](doc/rest.md#get-workspace-maps)

## v1.10.1
 2021-03-10
### Changes
- [#285](https://github.com/LayerManager/layman/issues/285) Fix upgrade 1.10.0 error (CSW get_template_path_and_values now works even if the layer is not in GeoServer and/or in DB).

## v1.10.0
 2021-03-04
### Upgrade requirements
- Set environment variables
  - [LAYMAN_QGIS_HOST](doc/env-settings.md#LAYMAN_QGIS_HOST)=nginx
  - [LAYMAN_QGIS_PORT](doc/env-settings.md#LAYMAN_QGIS_PORT)=80
  - [LAYMAN_QGIS_PATH](doc/env-settings.md#LAYMAN_QGIS_PATH)=/qgis/
  - [LAYMAN_QGIS_DATA_DIR](doc/env-settings.md#LAYMAN_QGIS_DATA_DIR)=/qgis/data/demo
- If you are running Layman with development settings, set environment variables
  - [LAYMAN_QGIS_HOST](doc/env-settings.md#LAYMAN_QGIS_HOST)=nginx-qgis
  - [LAYMAN_QGIS_PORT](doc/env-settings.md#LAYMAN_QGIS_PORT)=80
  - [LAYMAN_QGIS_PATH](doc/env-settings.md#LAYMAN_QGIS_PATH)=/qgis/
  - [LAYMAN_QGIS_DATA_DIR](doc/env-settings.md#LAYMAN_QGIS_DATA_DIR)=/qgis/data/dev
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.5.1`
    - If you are running Layman with development settings, run also `make client-build`.
- Run [standalone upgrade](README.md#upgrade) before starting Layman.
### Migrations and checks
- [#154](https://github.com/LayerManager/layman/issues/154) New column `style_type` in `publications` table is created.
- [#154](https://github.com/LayerManager/layman/issues/154) All workspaces are checked, that their name did not end with `_wms` and is not equal to `workspaces`. If there is any conflict found, startup process is stopped with error code 45. In that case, please downgrade to the previous minor release version and contact Layman contributors.
- [#154](https://github.com/LayerManager/layman/issues/154) All layers are copied into [dedicated WMS GeoServer workspace](doc/data-storage.md#geoserver). Styles are also moved into that workspace.
- [#154](https://github.com/LayerManager/layman/issues/154) Maps with URLs pointing to any layer stored in GeoServer are rewritten to dedicated [WMS workspace](doc/data-storage.md#geoserver).
- [#154](https://github.com/LayerManager/layman/issues/154) Following metadata properties are updated:
   - layers: [`wms_url`](doc/metadata.md#wms_url), [`graphic_url`](doc/metadata.md#graphic_url), [`identifier`](doc/metadata.md#identifier), [`layer_endpoint`](doc/metadata.md#layer_endpoint)
   - maps: [`graphic_url`](doc/metadata.md#graphic_url), [`identifier`](doc/metadata.md#identifier), [`map_endpoint`](doc/metadata.md#map_endpoint), [`map_file_endpoint`](doc/metadata.md#map_file_endpoint)
- [#154](https://github.com/LayerManager/layman/issues/154) Rename internal directories from `/users/{workspace}/layers/{layer}/input_sld` to `/users/{workspace}/layers/{layer}/input_style`
- [#154](https://github.com/LayerManager/layman/issues/154) Fill column `style_type` with `"sld"` for all layers.
### Changes
- [#154](https://github.com/LayerManager/layman/issues/154) Enable to publish QGIS layer styles (QML)
    - For endpoints [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer), parameter *sld* is replaced with the new parameter *style* and marked as deprecated. In response to endpoints [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer), *sld* is replaced by the new *style* item and marked as deprecated. Layman Test Client now uses *style* parameter.
    - Parameter *style* accepts also QGIS layer style (QML). Layman Test Client enables to select also `*.qml` files.
    - Endpoint [GET Workspace Layer](doc/rest.md#get-workspace-layer) returns in `style` attribute also `type`, either `"sld"` or `"qml"`.
    - Endpoint [GET Workspace Layer Style](doc/rest.md#get-workspace-layer-style) returns SLD style or QML style.
    - Treat attribute names in QML (also known as '[launder](https://gdal.org/drivers/vector/pg.html#layer-creation-options)').
    - New docker container with QGIS server called `qgis` in demo configuration.
    - New directory [LAYMAN_QGIS_DATA_DIR](doc/env-settings.md#LAYMAN_QGIS_DATA_DIR) is used to store [layer QGS files](doc/data-storage.md#filesystem).
    - [WMS](doc/endpoints.md#web-map-service) is moved to dedicated [GeoServer workspace](doc/data-storage.md#geoserver) whose name is composed from Layman's [workspace](doc/models.md#workspace) name and suffix `_wms`. [WFS](doc/endpoints.md#web-feature-service) remains in GeoServer workspace whose name is equal to Layman's workspace name.
    - Layers with [QGIS style](https://docs.qgis.org/3.16/en/docs/user_manual/style_library/style_manager.html#exporting-items) are published on [GeoServer dedicated WMS workspace](doc/data-storage.md#geoserver) through WMS cascade from QGIS server, where they are stored as QGS file. All layers are published directly from PostgreSQL database to GeoServer for [WFS workspace](doc/data-storage.md#geoserver).
    - SLD style published in dedicated WMS GeoServer workspace.
    - New environment variables [LAYMAN_QGIS_HOST](doc/env-settings.md#LAYMAN_QGIS_HOST), [LAYMAN_QGIS_PORT](doc/env-settings.md#LAYMAN_QGIS_PORT), [LAYMAN_QGIS_PATH](doc/env-settings.md#LAYMAN_QGIS_PATH), and [LAYMAN_QGIS_DATA_DIR](doc/env-settings.md#LAYMAN_QGIS_DATA_DIR).
    - Workspace name can not end with '_wms'. In such case, error with code 45 is raised.
    - During startup, [LAYMAN_OUTPUT_SRS_LIST](doc/env-settings.md#LAYMAN_OUTPUT_SRS_LIST) is ensured for all QGIS layers.
- [#67](https://github.com/LayerManager/layman/issues/67) Workspace-related [REST API endpoints](doc/rest.md) (maps, layers) were moved from `/rest/*` to `/rest/workspaces/*`. Whole path is for example: `/rest/workspaces/<workspace_name>/layers`. Old endpoints are marked as deprecated (with `Deprecation` header in response) and will be removed with next major release.
- [#99](https://github.com/LayerManager/layman/issues/99) New endpoint [GET Version](doc/rest.md#get-version). It is also available in Layman Test Client.
- Endpoint [GET Workspace Layer](doc/rest.md#get-workspace-layer) returns JSON object for **db_table** item. Previously incorrectly returns DB table name directly in **db_table** instead of *name* subitem.
- Undocumented attributes `type` and `id` were removed from GET Workspace Layer and Get Workspace Map responses.
- To indicated if Layman is running, you can call [GET Version](doc/rest.md#get-version).
- Optional [standalone upgrade](README.md#upgrade) command was implemented to avoid Gunicorn timeout.

## v1.9.1
 2021-01-18
### Upgrade requirements
- If you are migrating from v1.9.0 with `5514` included in [LAYMAN_OUTPUT_SRS_LIST](doc/env-settings.md#LAYMAN_OUTPUT_SRS_LIST), you need to manually replace definition of 5514 in `deps/geoserver/data/user_projections/epsg.properties` file with
    ```
    5514=PROJCS["S-JTSK / Krovak East North",GEOGCS["S-JTSK",DATUM["System Jednotne Trigonometricke Site Katastralni",SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],TOWGS84[572.213,85.334,461.94,4.9732,-1.529,-5.2484,3.5378],AUTHORITY["EPSG","6156"]],PRIMEM["Greenwich",0.0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.017453292519943295],AXIS["Geodetic longitude",EAST],AXIS["Geodetic latitude", NORTH],AUTHORITY["EPSG","4156"]],PROJECTION["Krovak",AUTHORITY["EPSG","9819"]],PARAMETER["latitude_of_center",49.5],PARAMETER["longitude_of_center",24.833333333333332],PARAMETER["azimuth", 30.288139722222223],PARAMETER["pseudo_standard_parallel_1",78.5],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",0.0],PARAMETER["false_northing",0.0],UNIT["m", 1.0],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","5514"]]
    ```
    and restart GeoServer.

### Changes
- [#228](https://github.com/LayerManager/layman/issues/228) Fixed shift in EPSG:5514.
- [#227](https://github.com/LayerManager/layman/issues/227) Flower is accessible in demo configuration again.

## v1.9.0
 2021-01-14
### Upgrade requirements
- Set environment variable [LAYMAN_OUTPUT_SRS_LIST](doc/env-settings.md#LAYMAN_OUTPUT_SRS_LIST) that contains list of EPSG codes that will appear as output spatial reference systems in both WMS and WFS. Choose any EPSG codes you need and add two mandatory systems `4326` and `3857`.
   - Sample SRS list for World: `4326,3857`
   - Sample SRS list for Czech Republic: `4326,3857,5514,102067,32633,32634`
   - Sample SRS list for Latvia: `4326,3857,3059`

  During startup, Layman passes definitions of each EPSG to GeoServer, either from its internal sources, or from [epsg.io](https://epsg.io/). If download from epsg.io fails, warning `Not able to download EPSG definition from epsg.io` appears in log. In such case, you can [set EPSG definition manually](https://docs.geoserver.org/2.13.0/user/configuration/crshandling/customcrs.html) and restart GeoServer.

  If you want to be sure that GeoServer understands each of your SRS that you passed into LAYMAN_OUTPUT_SRS_LIST, visit GeoServer's admin GUI, page Services > WMS or WFS, and click on Submit. If you see no error message, everything is OK.
  
  It can be also useful to generate output bounding box for every supported SRS in WMS Capabilities documents. You can control this in GeoServer's admin GUI, page Services > WMS, checkbox "Output bounding box for every supported CRS".
 
### Migrations
Data manipulations that automatically run at first start of Layman:
- [Data version table](doc/data-storage.md#data-version) is created. 
- GeoServer's security rules of each publication are recalculated according to publication's access rights. It fixes [#200](https://github.com/LayerManager/layman/issues/200) also for existing layers.
- Mistakenly created users and roles in GeoServer, created for public workspaces, are deleted.

### Changes
- One of [OAuth2 HTTP headers](doc/oauth2/index.md#request-layman-rest-api), `AuthorizationIssUrl`, is optional if and only if there is only one OAuth2 authorization server registered at Layman. The header was mandatory in 1.8.0 and sooner.
- Information about data version including migration ID is stored in [PostgreSQL](doc/data-storage.md#data-version).
- When public workspace is created, only workspace is created on GeoServer. Previously also user and roles were mistakenly created.

## v1.8.1
 2021-01-06
### Upgrade notes
- The fix of [#200](https://github.com/LayerManager/layman/issues/200) affects only newly posted or patched layers. To fix access rights on existing layers, you can either wait for 1.9 release (2021-01-15), or manually add ROLE_AUTHENTICATED for every [layer security rule](https://docs.geoserver.org/stable/en/user/security/layer.html) which already contains ROLE_ANONYMOUS.
### Changes
- [#200](https://github.com/LayerManager/layman/issues/200) Access rights EVERYONE is correctly propagated to GeoServer also for authenticated users. Only newly posted or patched layers are affected by the fix.
- One of [OAuth2 HTTP headers](doc/oauth2/index.md#request-layman-rest-api), `AuthorizationIssUrl`, is optional if and only if there is only one OAuth2 authorization server registered at Layman. The header was mandatory before 1.8.1 in any case.

## v1.8.0
 2020-12-14
### Upgrade requirements
- Set environment variable [LAYMAN_AUTHN_HTTP_HEADER_NAME](doc/env-settings.md#LAYMAN_AUTHN_HTTP_HEADER_NAME) that serves as a secret. Only combination of lowercase characters and numbers must be used for the value.
- Set environment variable [LAYMAN_PRIME_SCHEMA](doc/env-settings.md#LAYMAN_PRIME_SCHEMA). It is the name of the DB schema, so it is subject to the [restrictions given by PostgreSQL](https://www.postgresql.org/docs/9.2/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS). We recommend  value `_prime_schema` if possible.
- Replace LAYMAN_AUTHZ_MODULE environment variable with [GRANT_CREATE_PUBLIC_WORKSPACE](doc/env-settings.md#GRANT_CREATE_PUBLIC_WORKSPACE) and [GRANT_PUBLISH_IN_PUBLIC_WORKSPACE](doc/env-settings.md#GRANT_PUBLISH_IN_PUBLIC_WORKSPACE). The following settings correspond best with behaviour of previously used LAYMAN_AUTHZ_MODULE:
   - `LAYMAN_AUTHZ_MODULE=layman.authz.read_everyone_write_owner` (variable to remove)
      - `GRANT_CREATE_PUBLIC_WORKSPACE=` (new variable)
      - `GRANT_PUBLISH_IN_PUBLIC_WORKSPACE=` (new variable)
   - `LAYMAN_AUTHZ_MODULE=layman.authz.read_everyone_write_everyone` (variable to remove)
      - `GRANT_CREATE_PUBLIC_WORKSPACE=EVERYONE` (new variable)
      - `GRANT_PUBLISH_IN_PUBLIC_WORKSPACE=EVERYONE` (new variable)
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.4.1`
    - If you are running Layman with development settings, run also `make client-build`.
- Starting version 1.8, each user can have zero or one [personal workspaces](doc/models.md#personal-workspace), not more (in other words, one Liferay account can be linked with zero or one personal workspaces). Layman automatically checks this at first start. If two workspace linked to single user are fond, they are reported and Layman initialization is stopped. In such case, choose which one of reported workspaces should be the only personal workspace of the user, delete authn.txt file from the other workspace, and restart layman. The other workspace becomes public.
- If you are running Layman with development settings, run also `make timgen-build`.
### Changes
- We started to strictly distinguish [workspace](doc/models.md#workspace) as place, where publications are stored, and [user](doc/models.md#user) as representation of person in Layman system. This change was reflected in following places:
    - In REST API documentation, `username` was replaced with `workspace_name`. It's not breaking change, as it's only naming of part of URL path. 
    - Error messages and data, as well as Layman Test Client, also distinguishes workspace and user/username.
- Each workspace is now either [personal](doc/models.md#personal-workspace), or [public](doc/models.md#public-workspace). Personal workspace is automatically created when user reserves his username. Creation of and posting new publication to public workspaces is controlled by [GRANT_CREATE_PUBLIC_WORKSPACE](doc/env-settings.md#GRANT_CREATE_PUBLIC_WORKSPACE) and [GRANT_PUBLISH_IN_PUBLIC_WORKSPACE](doc/env-settings.md#GRANT_PUBLISH_IN_PUBLIC_WORKSPACE).
- [#28](https://github.com/LayerManager/layman/issues/28) It is possible to control also [read access](doc/security.md#publication-access-rights) to any publication per user.
   - New attribute `access_rights` added to [GET Workspace Layers](doc/rest.md#get-workspace-layers), [GET Workspace Layer](doc/rest.md#get-workspace-layer), [GET Workspace Maps](doc/rest.md#get-workspace-maps) and [GET Workspace Map](doc/rest.md#get-workspace-map) responses.
   - New parameters `access_rights.read` and `access_rights.write` added to [POST Workspace Layers](doc/rest.md#post-workspace-layers), [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer), [POST Workspace Maps](doc/rest.md#post-workspace-maps) and [PATCH Workspace Map](doc/rest.md#patch-workspace-map) requests. These new parameters are added to Test Client GUI.
   - Default values of access rights parameters (both read and write) of newly created publications are set to current authenticated user, or EVERYONE if published by anonymous.
- [#28](https://github.com/LayerManager/layman/issues/28) At first start of Layman, access rights of existing publications are set in following way:
    - [everyone can read and only owner of the workspace can edit](doc/security.md#Authorization) publications in [personal workspaces](doc/models.md#personal-workspace)
    - [anyone can read or edit](doc/security.md#Authorization) publications in [public workspaces](doc/models.md#public-workspace).
    - Security rules on GeoServer on [workspace level (workspace.*.r/w)](https://docs.geoserver.org/stable/en/user/security/layer.html) are deleted and replaced with security rules on [layer level (workspace.layername.r/w)](https://docs.geoserver.org/stable/en/user/security/layer.html) according to rules on Layman side.
- [#28](https://github.com/LayerManager/layman/issues/28) Only publications with [read access](doc/security.md#publication-access-rights) for EVERYONE are published to Micka as public.
- [#28](https://github.com/LayerManager/layman/issues/28) New REST endpoint [GET Users](doc/rest.md#get-users) with list of all users registered in Layman. This new endpoint was added to Test Client into tab "Others".
- [#28](https://github.com/LayerManager/layman/issues/28) [WMS endpoint](doc/endpoints.md#web-map-service) accepts same [authentication](doc/security.md#authentication) credentials (e.g. [OAuth2 headers](doc/oauth2/index.md#request-layman-rest-api)) as Layman REST API endpoints. It's implemented using Layman's WFS proxy. This proxy authenticates the user and send user identification to GeoServer.
- [#161](https://github.com/LayerManager/layman/issues/161) New method DELETE was implemented for endpoints [DELETE Workspace Maps](doc/rest.md#delete-workspace-maps) and [DELETE Workspace Layers](doc/rest.md#delete-workspace-layers).
- [#178](https://github.com/LayerManager/layman/issues/178) New attribute `screen_name` is part of response for [GET Users](doc/rest.md#get-users) and [Get Current User](doc/rest.md#get-current-user).
- [#178](https://github.com/LayerManager/layman/issues/178) LifeRay attribute `screen_name` is preferred for creating username in Layman. Previously it was first part of email.
- Attribute `groups` is no longer returned in [GET Workspace Map File](doc/rest.md#get-workspace-map-file) response.
- [#28](https://github.com/LayerManager/layman/issues/28) New environment variable [LAYMAN_PRIME_SCHEMA](doc/env-settings.md#LAYMAN_PRIME_SCHEMA). 

## v1.7.4
2020-12-14
### Changes
- [#175](https://github.com/LayerManager/layman/issues/175) Fix posting new layer caused by [v1.7.3](#v173).

## v1.7.3
2020-11-30
### :warning: Attention :warning:
There is a critical bug in this release, posting new layer breaks Layman: https://github.com/LayerManager/layman/issues/175 It's solved in [v1.7.4](#v174).

### Changes
- If published [layer](doc/models.md#layer) has empty bounding box (i.e. no features), its bounding box on WMS/WFS endpoint is set to the whole World. This happens on [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer).
- [#40](https://github.com/LayerManager/layman/issues/40) Enable to upload empty ShapeFile.

## v1.7.2
2020-11-09
### Changes
- [#133](https://github.com/LayerManager/layman/issues/133) Attribute `url` of [GET Workspace Maps](doc/rest.md#get-workspace-maps) response was repaired. Previously, it incorrectly used map name instead of username in the URL path.

## v1.7.1
2020-09-30
### Upgrade requirements
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.3.0`
    - If you are running Layman with development settings, run also `make client-build`.
### Changes
- Test Client contains also GET Workspace Layer Style endpoint.
- Return real SLD style in GET Workspace Layer Style instead of just metadata
- [#109](https://github.com/LayerManager/layman/issues/109) Handle records without title in GET Workspace Layers / GET Workspace Maps

## v1.7.0
2020-09-30
### Upgrade requirements
- [#65](https://github.com/LayerManager/layman/issues/65) Set environment variable [LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE](doc/env-settings.md#LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE). Only combination of lowercase characters and numbers must be used for the value.
- [#101](https://github.com/LayerManager/layman/issues/101) Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) from `v1.1.2` to `v1.2.0`
    - If you are running Layman with development settings, run also `make client-build`.
### Changes
- [#65](https://github.com/LayerManager/layman/issues/65) [WFS endpoint](doc/endpoints.md#web-feature-service) accepts same [authentication](doc/security.md#authentication) credentials (e.g. [OAuth2 headers](doc/oauth2/index.md#request-layman-rest-api)) as Layman REST API endpoints. It's implemented using Layman's WFS proxy. This proxy authenticates the user and send user identification to GeoServer. In combination with changes in v1.6.0, Layman's [`read-everyone-write-owner` authorization](doc/security.md#authorization) (when active) is propagated to GeoServer and user can change only hers layers.
- [#88](https://github.com/LayerManager/layman/issues/88) Attribute **title** was added to REST endpoints [GET Workspace Layers](doc/rest.md#get-workspace-layers) and [GET Workspace Maps](doc/rest.md#get-workspace-maps).
- [#95](https://github.com/LayerManager/layman/issues/95) When calling WFS Transaction, Layman will automatically create missing attributes in DB before redirecting request to GeoServer. Each missing attribute is created as `VARCHAR(1024)`. Works for WFS-T 1.0, 1.1 and 2.0, actions Insert, Update and Replace. If creating attribute fails for any reason, warning is logged and request is redirected nevertheless.
- [#96](https://github.com/LayerManager/layman/issues/96) New REST API endpoint [GET Workspace Layer Style](doc/rest.md#get-workspace-layer-style) is created, which returns Layer default SLD. New attribute ```sld.url``` is added to [GET Workspace Layer endpoint](doc/rest.md#get-workspace-layer), where URL of Layer default SLD can be obtained. It points to above mentioned [GET Workspace Layer Style](doc/rest.md#get-workspace-layer-style).
- [#101](https://github.com/LayerManager/layman/issues/101) Test Client has new page for WFS proxy and is capable to send authenticated queries.
- [#65](https://github.com/LayerManager/layman/issues/65) Layman automatically setup [HTTP authentication attribute](https://docs.geoserver.org/stable/en/user/security/tutorials/httpheaderproxy/index.html) and chain filter at startup. Secret value of this attribute can be changed in [LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE](doc/env-settings.md#LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE) and is used by Layman's WFS proxy.

## v1.6.1
2020-08-19
- [#97](https://github.com/LayerManager/layman/issues/97) Before v1.6, [reserved `username`](doc/rest.md#patch-current-user) could be the same as LAYMAN_GS_USER. Starting at 1.6, this leads to conflict of two GeoServer users with the same name. This patch release comes with detection of this conflict (Layman error code 41).
   - If you encounter error 41, you can resolve the conflict by following steps:
       - In GeoServer GUI, create new GeoServer user with another name to become new LAYMAN_GS_USER and give him LAYMAN_GS_ROLE and ADMIN roles
       - In GeoServer GUI, remove the old LAYMAN_GS_USER user
       - Change environment settings LAYMAN_GS_USER and LAYMAN_GS_PASSWORD for the new GeoServer user
       - Restart Layman

## v1.6.0
2020-08-19
### Upgrade requirements
- [#69](https://github.com/LayerManager/layman/issues/69) If you are running Layman with development or test settings, set [LAYMAN_SETTINGS_MODULE](doc/env-settings.md#LAYMAN_SETTINGS_MODULE) in your `.env` file to `layman_settings`. No action is required if you are running Layman based on demo settings (probably all production instances).
### Changes
- [#74](https://github.com/LayerManager/layman/issues/74) Layman user and role at GeoServer defined by [LAYMAN_GS_USER](doc/env-settings.md#LAYMAN_GS_USER) and [LAYMAN_GS_ROLE](doc/env-settings.md#LAYMAN_GS_ROLE) are now created automatically on Layman's startup if an only if new environment variable [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) is provided. There is no need to set [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) for other reason than automatically creating Layman user and Layman role.
   - No change is required. If you are migrating existing instance, Layman user and role are already created, so you don't need to set [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD). If this is your first Layman release, [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) is set in `.env` files starting with this version, so Layman user and role at GeoServer will be automatically created on startup.
   - No need to run command `make geoserver-reset-default-datadir` from now on. This command was removed from make options.
- [#62](https://github.com/LayerManager/layman/issues/62) GeoServer [Proxy Base URL](https://docs.geoserver.org/stable/en/user/configuration/globalsettings.html) is now automatically set on Layman's startup according to [LAYMAN_GS_PROXY_BASE_URL](doc/env-settings.md#LAYMAN_GS_PROXY_BASE_URL). If you do not set the variable, value is calculated as [LAYMAN_CLIENT_PUBLIC_URL](doc/env-settings.md#LAYMAN_CLIENT_PUBLIC_URL)+[LAYMAN_GS_PATH](doc/env-settings.md#LAYMAN_GS_PATH). If you set it to empty string, no change of Proxy Base URL will be done on GeoServer side.
- [#83](https://github.com/LayerManager/layman/issues/89) All layers are created as `GEOMETRY` type, so any other type can be added (for example polygons can be added to points).
- [#73](https://github.com/LayerManager/layman/issues/73) Layman users are automatically created on GeoServer (either at start up of Layman or when reserved) with separate role and workspace. Username is the same as in Layman, name of role is `"USER_"+username`, name of workspace is the same as username. Read and write permissions for workspace are set according to Layman's authorization (as of now read-everyone-write-everyone or read-everyone-write-owner).
- New environment variables [LAYMAN_GS_USER_GROUP_SERVICE](doc/env-settings.md#LAYMAN_GS_USER_GROUP_SERVICE) and [LAYMAN_GS_ROLE_SERVICE](doc/env-settings.md#LAYMAN_GS_ROLE_SERVICE) enable to control which user/group and role services are used at GeoServer. Not setting these variables means to use default services. 
- [#69](https://github.com/LayerManager/layman/issues/69) Three separate identical settings files (`layman_settings_demo.py`, `layman_settings_dev.py`, `layman_settings_test.py`) were merged into one file `layman_settings.py`.
- If username used in REST API request path is not yet reserved, HTTP requests other than POST returns (e.g. GET) HTTP error 404 (Layman code 40). Previously in case of GET request, empty list was returned.
- List of GeoServer reserved workspace names was moved from `layman_settings.py` into source code (`src\layman\common\geoserver\__init__.py`)
- Undocumented authentication module `layman.authn.url_path.py` that was unused for a long time, was removed.
- Python setting [`PG_NON_USER_SCHEMAS`](src/layman_settings.py) is now more explicit about forbidden schema names.


## v1.5.0
2020-06-18
- Metadata records are published in SOAP envelope of CSW and they are published on Micka as "Public".
- Upgrade Micka to version v2020.014. All versions between v2020.010 and v2020.014 should work well with Layman. If you are running other version than v2020.014, you can now set environment variable [MICKA_ACCEPTED_VERSION](doc/env-settings.md#MICKA_ACCEPTED_VERSION) to your version so that Layman accepts your version on startup. 
- New environment variable [MICKA_ACCEPTED_VERSION](doc/env-settings.md#MICKA_ACCEPTED_VERSION)


## v1.4.0
2020-04-23
- Update Python dependencies
- Add [`md_language`](doc/metadata.md#md_language) metadata property
- Guess metadata properties
  - [`md_language`](doc/metadata.md#md_language) of both Layer and Map using pycld2 library
  - [`language`](doc/metadata.md#language) of Layer using pycld2 library
  - [`scale_denominator`](doc/metadata.md#scale_denominator) of Layer using distanced between vertices
- Change multiplicity of [`language`](doc/metadata.md#language) metadata property from `1` to `1..n` according to XML Schema
- Remove [`language`](doc/metadata.md#language) metadata property from Map according to XML Schema
- Build Layman as a part of `make start-demo*` commands.
- Run demo without Micka, fix #55
- Respect public URL scheme in REST API responses, fix #58
- Show public WMS and WFS URLs in metadata comparison, fix #54
- Change WFS endpoint from `/ows` to `/wfs`, because `/ows` capabilities pointed to `/wfs`


## v1.3.3
2020-04-15
### Upgrade requirements
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) from `v1.1.1` to `v1.1.2`
### Changes
- Upgrade Layman test client to version 1.1.2, fixing reaching `static.css` without authentication
- Extend map JSON schema with ArcGIS REST API layers and static image layers


## v1.3.2
2020-04-09
- Request Geoserver through http instead of public scheme, fix #57


## v1.3.1
2020-03-30
- Post metadata record if no one found during patch, fix #52
- Use EPSG:3857 bbox when generating thumbnail, fix #53


## v1.3.0
2020-03-29
### Upgrade requirements
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) from `v1.0.0` to `v1.1.1`
- Remove [CSW_ORGANISATION_NAME_REQUIRED](https://github.com/LayerManager/layman/blob/v1.2.1/doc/env-settings.md) from environment settings
- If you are using Layman's `make` commands with `-d` suffix, use these commands without the `-d` suffix from now on (e.g. `make start-demo-full-d` becomes `make start-demo-full`).

### Changes
- Both [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) and [PATCH Workspace Map](doc/rest.md#patch-workspace-map) automatically update also CSW metadata records.
- Use absolute URLs in responses of Layer and Map endpoints
- Add [GET Workspace Layer Metadata Comparison](doc/rest.md#get-workspace-layer-metadata-comparison) and [GET Workspace Map Metadata Comparison](doc/rest.md#get-workspace-map-metadata-comparison) endpoints. 
- Add [`revision_date`](doc/metadata.md#revision_date) metadata property
- Add `metadata.comparison_url` to [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [GET Workspace Map](doc/rest.md#get-workspace-map) responses.
- Upgrade Layman test client to version 1.1.1
- Environment settings [CSW_ORGANISATION_NAME_REQUIRED](https://github.com/LayerManager/layman/blob/v1.2.1/doc/env-settings.md) is not used anymore as Micka v2020 accepts records without organisation names. 
- Metadata properties [wms_url](doc/metadata.md#wms_url) and [wfs_url](doc/metadata.md#wfs_url) point directly to GetCapabilities documents. 
- Layman now uses WMS 1.3.0 and WFS 2.0.0 in communication with GeoServer and in CSW metadata records.
- All `make` commands with `docker-compose up` now run in the background. Foreground running was removed. Use `docker logs` to inspect container logs. 
 

## v1.2.1
2020-03-20
### Upgrade requirements
- Change [CSW_URL](doc/env-settings.md#CSW_URL) from `http://micka:80/csw` to `http://micka:80/micka/csw`

### Changes
- Fix URL prefix of Micka GUI in Layman v1.2.0, [#49](https://github.com/LayerManager/layman/issues/49) 

## v1.2.0
2020-03-18

### Upgrade requirements
- Upgrade Micka to [v2020.010](https://github.com/hsrs-cz/Micka/releases/tag/v2020.010).
- Add [CSW_PROXY_URL](doc/env-settings.md#CSW_PROXY_URL) to distinguish between internal CSW URL for Layman and public CSW URL for clients.
- Rename host of [LAYMAN_TIMGEN_URL](doc/env-settings.md#LAYMAN_TIMGEN_URL) from `hslayers` to `timgen`.
- Add [MICKA_HOSTPORT](doc/env-settings.md#MICKA_HOSTPORT) for demo run.

### Changes
- Publish metadata record of [map](doc/models.md#map) to Micka on [POST Workspace Maps](doc/rest.md#post-workspace-maps).
- Add `metadata` info to [GET Workspace Map](doc/rest.md#get-workspace-map) response.
- Extend `metadata` info with `identitier` attribute in case of both layer and map.
- Add documentation of [map metadata properties](doc/metadata.md)
- Use `metadataStandardName` and `metadataStandardVersion` in metadata templates
- Adjust metadata XML instead of using string formatting
- Rename metadata properties. All metadata-record-related properties have `md_` prefix. Dataset-related properties do not have any special prefix.

    |Old name|New name|
    |---|---|
    |`data_identifier`|`identifier`|
    |`data_organisation_name`|`organisation_name`|
    |`dataset_language`|`language`|
    |`date`|`publication_date`|
    |`date_stamp`|`md_date_stamp`|
    |`file_identifier`|`md_file_identifier`|
    |`organisation_name`|`md_organisation_name`|

- Add LaymanError 38 (Micka HTTP or connection error)
- Treat attribute names in SLD (aka 'launder'), [#45](https://github.com/LayerManager/layman/issues/45)
- Fix Micka's About URL in wait_for_deps
- Assert version of Micka on startup.
- Load data into redis on startup even in Flower.
- Better handle Micka's HTTP errors, [#43](https://github.com/LayerManager/layman/issues/43)
- Rename hslayers container to timgen (Thumbnail Image Generator)

## v1.1.8
2020-03-16
- Treat attribute names in SLD (aka 'launder'), [#45](https://github.com/LayerManager/layman/issues/45)
- Fix Micka's About URL in wait_for_deps

## v1.1.7
2020-03-09
- Assert version of Micka on startup.

## v1.1.6
2020-03-02
- Mute 500 error on CSW delete.

## v1.1.5
2020-02-28

Prior to 1.1.5, existing usernames, layers and maps **were not imported sometimes** on Layman's startup, that made it appear as they are missing. It should be fixed now by loading data into redis on startup even in Flower container.

## v1.1.4
2020-02-19
- Better handle Micka's HTTP errors, [#43](https://github.com/LayerManager/layman/issues/43)

## v1.1.3
2020-01-31
- Improve documentation of [enviroment variables](doc/env-settings.md)
- Show real info instead of just SUCCESS status in successfully finished tasks within GET Workspace Layer, GET Workspace Map, etc.
- Check freshness of links and image URLs in documentation within CI
- Add few words about Layman in [EN](doc/about.md) ans [CS](doc/cs/o-aplikaci.md)

## v1.1.2
2019-12-26
- Allow requesting layman from other docker containers (fix [#38](https://github.com/LayerManager/layman/issues/38))

## v1.1.1
2019-12-23
- Fix PENDING in state after celery task is removed from redis

## v1.1.0
2019-12-23
- Publish metadata record of [layer](doc/models.md#layer) to Micka on [POST Workspace Layers](doc/rest.md#post-workspace-layers). Connection to Micka is configurable using [CSW_*](doc/env-settings.md) environment variables.
- Delete metadata record of layer from Micka on [DELETE Workspace Layer](doc/rest.md#delete-workspace-layer).
- Add `metadata` info to [GET Workspace Layer](doc/rest.md#get-workspace-layer) response, including CSW URL and metadata record URL.
- [Documentation of metadata](doc/metadata.md)
- [LAYMAN_PROXY_SERVER_NAME](doc/env-settings.md#LAYMAN_PROXY_SERVER_NAME) environment variable
- Do not depend on specific version of chromium-browser and chromedriver
- Save write-lock to redis on POST, PATCH and DELETE of Layer and Map
- Enable to run Layman using multiple WSGI Flask processes by moving information about tasks from memory to redis
- Use Flask decorators
- Unify async task names, call task methods in the same way (src/layman/common/tasks.py#get_task_methods, src/layman/common/tasks.py#get_task_methods#tasks_util.get_chain_of_methods, src/layman/celery.py#set_publication_task_info)
