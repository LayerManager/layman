# Changelog

## v3.0.0
 {release-date}
### Upgrade requirements
- Only versions 2.0.0 and newer can be upgraded to this version. For older versions, please upgrade to last 2.1.x first.
- If you have any `Pipfile*` files in the root directory of this repository, they can be deleted.
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=0dc72e6b0022f0902fb857106f46fccef94f95ad
  ```
### Migrations and checks
#### Schema migrations
#### Data migrations
- [#1126](https://github.com/LayerManager/layman/issues/1126) Migrate graphic URLs in map metadata from workspace&name-based format to UUID-based format.
- [#1126](https://github.com/LayerManager/layman/issues/1126) Migrate graphic URLs in layer metadata from workspace&name-based format to UUID-based format.

### Changes
- [#1126](https://github.com/LayerManager/layman/issues/1126) Endpoint [GET Workspace Map Thumbnail](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-map-thumbnail) was removed and replaced with endpoint [GET Map Thumbnail](doc/rest.md#get-map-thumbnail) endpoint to use UUID-based URL `/rest/maps/{uuid}/thumbnail` instead of workspace&name-based URL.
- [#1126](https://github.com/LayerManager/layman/issues/1126) Endpoint [GET Workspace Layer Thumbnail](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-layer-thumbnail) was removed and replaced with endpoint [GET Layer Thumbnail](doc/rest.md#get-layer-thumbnail) endpoint to use UUID-based URL `/rest/layers/{uuid}/thumbnail` instead of workspace&name-based URL.
- [#1126](https://github.com/LayerManager/layman/issues/1126) Endpoint [GET Workspace Map File](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-map-file) was removed and replaced with endpoint [GET Map File](doc/rest.md#get-map-file) to use UUID-based URL `/rest/map/{uuid}/file` instead of workspace&name-based URL.

## v2.1.0
 2025-05-02
### Changes
- [#1124](https://github.com/LayerManager/layman/issues/1124) Upgrade GeoServer to 2.26.2.

## v2.0.0
 2025-03-26
### Upgrade requirements
- Only versions 1.23.2 and newer can be upgraded to this version. For older versions, please upgrade to last 1.23.x first.
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v2.0.0
  ```
- Set new environment variable [GRANT_DELETE_OTHER_USER](doc/env-settings.md#GRANT_DELETE_OTHER_USER), e.g. to empty value:
  ```
  GRANT_DELETE_OTHER_USER=
  ```
- In demo configuration, build QGIS v3.40.4 image using command
  ```
  docker compose -f docker-compose.deps.demo.yml build qgis
  ```
### Migrations and checks
#### Schema migrations
- [#1009](https://github.com/LayerManager/layman/issues/1009) Add column `description` to table `publications` in prime DB schema.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Add column `created_at` to table `publications` in prime DB schema.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Add column `layer_uuid` to table `map_layer` in prime DB schema.
#### Data migrations
- [#1009](https://github.com/LayerManager/layman/issues/1009) Fill column `description` in `publications` table in prime DB schema. Value is taken from GeoServer for layers and from filesystem for maps.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Fill column `created_at` in `publications` table in prime DB schema. Value is taken from filesystem `uuid.txt` file creation. `uuid.txt` file is subsequently deleted.
- [#1048](https://github.com/LayerManager/layman/issues/1048) New schema `layers` is created in [database](doc/data-storage.md#postgresql).
- [#1048](https://github.com/LayerManager/layman/issues/1048) New workspaces [`layman` and `layman_wms`](doc/data-storage.md#geoserver) are created on GeoServer, each with PostgreSQL data store `postgresql`.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Layers, whose `wfs_wms_status` is not `AVAILABLE`, are deleted.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Relations in prime DB schema table `map_layer` are migrated from columns `layer_workspace` and `layer_name` into column `layer_uuid`. Columns  `layer_workspace` and `layer_name` are subsequently dropped and column `layer_uuid` is set to `NOT NULL`.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Most layer data is moved, renamed and/or re-created:
  - layers files are moved to [new paths](doc/data-storage.md#filesystem) derived from `uuid`
  - internal layer tables are moved to [database schema `layers`](doc/data-storage.md#postgresql), index and sequence names are derived from `uuid` (table name already was)
  - GeoServer layers are re-created with [new names](doc/data-storage.md#geoserver) derived from `uuid`
  - WMS and WFS references are updated in existing CSW metadata records.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Map files are moved to [new paths](doc/data-storage.md#filesystem) with new names derived from `uuid` and referenced internal layers' url and names are changed to the new ones.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Some workspace-related data is removed:
  - GeoServer workspaces `<layman_workspace_name>` and `<layman_workspace_name>_wms` per each [Layman workspace](doc/models.md#workspace)
  - database schemas `<layman_workspace_name>` per each [Layman workspace](doc/models.md#workspace)
  - directory `LAYMAN_QGIS_DATA_DIR/workspaces`
  - directory `LAYMAN_NORMALIZED_RASTER_DATA_DIR/workspaces`
  - directory `LAYMAN_DATA_DIR/workspaces`
### Changes
- [#1048](https://github.com/LayerManager/layman/issues/1048) Many names, identifiers, and references of [layers](doc/models.md#layer) and [maps](doc/models.md#map) are now derived from `uuid` instead of Layman workspace and name. Entities that represented Layman workspaces are suppressed.
  - Names of [files and directories](doc/data-storage.md#filesystem) are derived from publication `uuid`. Workspace directories are not used anymore.
  - All layer tables are stored in [`layers` DB schema](doc/data-storage.md#postgresql). Workspace schemas are not used anymore.
  - Names of [Feature types, Coverages, Layers and Styles in GeoServer WFS and WMS workspaces](doc/data-storage.md#geoserver) are derived from layer `uuid` (i.e. `l_<UUID>`). All GeoServer entities are created in two global workspaces (`layman` for WFS layers and `layman_wms` for WMS layers), instead of separate workspaces for each Layman workspace.
  - Metadata properties [wfs_url](doc/metadata.md#wfs_url) and [wms_url](doc/metadata.md#wms_url) contain new layer names `l_<UUID>`.
  - Layer in map JSON file is considered [internal](doc/models.md#internal-map-layer) if named `l_<UUID>` and located in GeoServer workspace `layman` or `layman_wms`.
- [#1048](https://github.com/LayerManager/layman/issues/1048) New keys `wfs.name` and `wms.name` were added to [GET Workspace Layer](doc/rest.md#get-workspace-layer) response. Use values from these keys when communicating with WFS and WMS.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Actions [POST Workspace Maps](doc/rest.md#post-workspace-maps) and [PATCH Workspace Map](doc/rest.md#patch-workspace-map) raises error if there is internal layer referenced by its Layman name and Layman workspace instead of new GeoServer name `l_<UUID>` and new GeoServer workspace `layman` or `layman_wms`.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Layers with QML style are named by their title instead of name in WMS graphical legend.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Keys `file.paths`, `file.path` and `thumbnail.path` of GET Workspace [Layer](doc/rest.md#get-workspace-layer)/[Map](doc/rest.md#get-workspace-map) are relative to [LAYMAN_DATA_DIR](doc/env-settings.md#layman_data_dir) instead of workspace directory.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Stop saving publication UUID to `uuid.txt` file.
- [#1048](https://github.com/LayerManager/layman/issues/1048) Information about layer in WMS and WFS (e.g. keys `wms` and `wfs` in [GET Workspace Layer](doc/rest.md#get-workspace-layer)) is obtained from GeoServer REST API instead of WMS GetCapabilities to improve speed.
- [#1048](https://github.com/LayerManager/layman/issues/1048) POST Workspace [Layers](doc/rest.md#post-workspace-layers)/[Maps](doc/rest.md#post-workspace-maps) accepts new optional body parameter `uuid`. It's meant mostly for testing purposes.
- [#161](https://github.com/LayerManager/layman/issues/161) New method [DELETE User](doc/rest.md#delete-user) allows users to delete user accounts.
- [#942](https://github.com/LayerManager/layman/issues/942) New key `used_in_maps` was added to responses of requests [GET Publications](doc/rest.md#get-publications), [GET Layers](doc/rest.md#get-layers), [GET Workspace Layers](doc/rest.md#get-workspace-layers), and [GET Workspace Layer](doc/rest.md#get-workspace-layer). It can be used to warn user before deleting layer that the layer is used in some maps.
- [#1009](https://github.com/LayerManager/layman/issues/1009) PATCH Workspace [Layer](doc/rest.md#patch-workspace-layer)/[Map](doc/rest.md#patch-workspace-map) returns same response as POST Workspace [Layers](doc/rest.md#post-workspace-layers)/[Maps](doc/rest.md#post-workspace-maps) with only `name`, `uuid`, `url` and for Layer also optional `files_to_upload` keys.
- [#1009](https://github.com/LayerManager/layman/issues/1009) Updating Micka record as part of PATCH Workspace [Layer](doc/rest.md#patch-workspace-layer) runs asynchronously to make PATCH request faster.
- [#909](https://github.com/LayerManager/layman/issues/909) Upgrade QGIS Server from v3.32.2 to v3.40.4. Also use docker hub repo [layermanager/qgis-server](https://hub.docker.com/r/layermanager/qgis-server) instead of jirikcz/qgis-server,
  - QML styles up to v3.40.2 are supported.
  - [#270](https://github.com/LayerManager/layman/issues/270) Precision error of EPSG:5514 in QGIS WMS GetMap was partially fixed with following exceptions: if data CRS is EPSG:5514 and WMS GetMap CRS is EPSG:4326 or CRS:84, or vice versa, the precision error is now about 3.2 m (it was 0.5 m in v3.32.2).
- [#1039](https://github.com/LayerManager/layman/issues/1039) Deprecated endpoint, parameters and keys were removed:
  - key `file_type` was removed from endpoints GET [Publications](doc/rest.md#get-publications)/[Layers](doc/rest.md#get-layers)/[Workspace Layers](doc/rest.md#get-workspace-layers)/[Workspace Layer](doc/rest.md#get-workspace-layer) response
  - key `file`.`path` was removed from GET [Workspace Layer](doc/rest.md#get-workspace-layer) response
  - key `sld` was removed from GET [Workspace Layer](doc/rest.md#get-workspace-layer) response
  - key `db_table` was removed from GET [Workspace Layer](doc/rest.md#get-workspace-layer) response
  - key `data`.`layman`.`last-migration` was removed from [GET Version](doc/rest.md#get-version) response
  - body parameter `sld` was removed from [POST Workspace Publications](doc/rest.md#post-workspace-layers) and [PATCH Workspace Publication](doc/rest.md#patch-workspace-layer)
  - workspace-related endpoints which did not include `/workspaces` in their path were removed 
- [#701](https://github.com/LayerManager/layman/pull/701) Check bounding bbox of normalized raster before posting to GeoServer. Stop checking that Layer is available in WMS/WFS GetCapabilities after publishing to GeoServer.
- Output from `make upgrade-demo` and `make upgrade-demo-full` is saved to `tmp/logs/demo_upgrade_${date -u +"%FT%H%MZ"}.log`. The output is also written to standard output.
- Add forgotten `thumbnail.path` attributes to documentation of GET Workspace [Layer](doc/rest.md#get-workspace-layer)/[Map](doc/rest.md#get-workspace-map) responses.
- Upgrade GeoServer to 2.21.4.
- [#1028](https://github.com/LayerManager/layman/issues/1028) Upgrade Node.js of Laymen Test Client from v18 to v22 and dependencies:
  - eslint-config-next 13 -> 14
  - next 13 -> 14
  - semantic-ui-react 2 -> 3.0.0-beta.2
- [#1028](https://github.com/LayerManager/layman/issues/1028) Upgrade Python dependencies
  - attrs 23.1.0 -> 24.3.0
  - certifi 2023.11.17 -> 2024.12.14 (suggested by dependabot)
  - flask 3.0.0 -> 3.0.3
  - gunicorn 20.1.0 -> 22.0.0 (suggested by dependabot)
  - idna 3.6 -> 3.10 (suggested by dependabot)
  - importlib-metadata 7.0.0 -> 8.4.0
  - jinja2 3.1.2 -> 3.1.4 (suggested by dependabot)
  - jsonschema 4.20.0 -> 4.23.0
  - lxml 4.9.3 -> 5.3.0
  - owslib 0.29.3 -> 0.31.0
  - pillow 10.1.0 -> 10.4.0 (suggested by dependabot)
  - pipenv 2020.11.15 -> 2024.4.0
  - pytz 2023.3.post1 -> 2024.2
  - requests 2.31.0 -> 2.32.0
  - tornado 6.4.0 -> 6.4.2 (suggested by dependabot)
  - urllib3 2.31.0 -> 2.32.0 (suggested by dependabot)
  - werkzeug 3.0.1 -> 3.0.6 (suggested by dependabot)
  - zipp 3.17.0 -> 3.19.1 (suggested by dependabot)
- [#798](https://github.com/LayerManager/layman/issues/798) Upgrade Node.js of Timgen from v16 to v22 and dependencies:
  - encodeurl 1 -> 2
  - express 4.18 -> 4.21
  - http-proxy-middleware 2.0.6 -> 2.0.7
  - vite 3.2.7 -> 3.2.11
- Unify names of GitHub Actions, make targets and shell scripts for tests.
- All changes from [v1.23.1](#v1231) and [v1.23.2](#v1232).

## v1.23.2
 2024-03-10
### Upgrade requirements
- [#1021](https://github.com/LayerManager/layman/issues/1021) After [upgrade](README.md#upgrade) and start of Layman, it's needed to change GeoServer configuration by following steps:
    1. Log in to GeoServer Admin
    2. Click on **Security** > **Authentication**
    3. Find part "**Authentication Filters**" and click on "**laymanHttpHeader**"
    4. In part "**Role source**" choose "**Role service**" in left dropdown and "**layman_role_service**" in right dropdown.
    5. Click on **Save** button.
### Changes
- [#1021](https://github.com/LayerManager/layman/issues/1021) Fix WFS-T error by manually changing GeoServer configuration as described in upgrade requirements.
- [#1022](https://github.com/LayerManager/layman/issues/1022) Fix login in demo configuration with authentication. 

## v1.23.1
 2024-03-06
### Changes
- [#1016](https://github.com/LayerManager/layman/issues/1016) Flower and Celery worker containers used to wait for all dependencies and also check [role service](doc/security.md#role-service), from now on it waits only for Layman API to be ready.
- [#165](https://github.com/LayerManager/layman/issues/165) Roles in REST endpoint [GET Roles](doc/rest.md#get-roles) result are in alphabetical order.

## v1.23.0
 2024-01-30
### Upgrade requirements
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.18.0
  ```
- Stop using environment variable `LAYMAN_GS_ROLE_SERVICE`, it has no effect to Layman anymore. Layman now uses [role service](doc/security.md#role-service) identified by new environment variable [LAYMAN_ROLE_SERVICE_URI](doc/env-settings.md#LAYMAN_ROLE_SERVICE_URI). The service is called `layman_role_service` on GeoServer.
- Set new environment variable [LAYMAN_ROLE_SERVICE_URI](doc/env-settings.md#LAYMAN_ROLE_SERVICE_URI)
- Stop using environment variable [`OAUTH2_INTROSPECTION_SUB_KEY`](https://github.com/LayerManager/layman/blob/v1.22.3/doc/env-settings.md#oauth2_introspection_sub_key), it has no effect to Layman anymore. 
- If you are using Wagtail as OAuth2 provider
  - After running `make upgrade-demo` or `make upgrade-demo-full`, run also script `v1_23_change_oauth2_sub_username_to_user_id.py`:
    ```bash
    docker compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml run --rm --no-deps -u root -e LAYMAN_WAGTAIL_DB_URI=<URI_of_Wagtail_db> layman bash -c "cd src && python3 -B v1_23_change_oauth2_sub_username_to_user_id.py"
    ```
      - `URI_of_Wagtail_db` is PostgreSQL connection URI to Wagtail database, e.g. `postgresql://user:password@host.docker.internal:5432/wagtail_db_name`
      - The script changes OAuth2 "sub" values in Layman prime DB schema from Wagtail usernames to Wagtail user IDs. See [940](https://github.com/LayerManager/layman/issues/940).
### Migrations and checks
#### Schema migrations
- [#165](https://github.com/LayerManager/layman/issues/165) Add column `role_name` to table `rights` in prime DB schema. Add constraint that exactly one of columns `role_name` and `id_user` is not null.
- [#165](https://github.com/LayerManager/layman/issues/165) Create DB schema `_role_service` that can be used as [role service](doc/security.md#role-service).
- [#165](https://github.com/LayerManager/layman/issues/165) Column `name` in table `workspaces` in prime DB schema length is changed to 59 characters.
- Drop DB table `right_types`.
#### Data migrations
- [#165](https://github.com/LayerManager/layman/issues/165) Delete technical roles and user-role relations in GeoServer `default` role service, which is now replaced by JDBC role service.
### Changes
- [#165](https://github.com/LayerManager/layman/issues/165) Prior to this version, Layman enabled to use [usernames](doc/models.md#username) and pseudo-role `EVERYONE` in access rights. From now on, Layman accepts also [role names](doc/models.md#role).
- [#165](https://github.com/LayerManager/layman/issues/165) Roles (except of `EVERYONE`) are managed by [role service](doc/security.md#role-service).
- [#165](https://github.com/LayerManager/layman/issues/165) New REST endpoint [GET Roles](doc/rest.md#get-roles) with list of all roles registered in [role service](doc/security.md#role-service), that can be used in access rights.
  - This new endpoint was added to Test Client into tab "Others".
- [#165](https://github.com/LayerManager/layman/issues/165) POST Workspace [Layers](doc/rest.md#post-workspace-layers)/[Maps](doc/rest.md#post-workspace-maps) and PATCH Workspace [Layer](doc/rest.md#patch-workspace-layer)/[Map](doc/rest.md#patch-workspace-map) saves [role names](doc/models.md#role) mentioned in `access_rights.read` and `access_rights.write` parameters into [prime DB schema](doc/data-storage.md#postgresql).
- [#165](https://github.com/LayerManager/layman/issues/165) Many requests respect roles in access rights:
  - [GET](doc/rest.md#get-workspace-layer)/[PATCH](doc/rest.md#patch-workspace-layer)/[DELETE](doc/rest.md#delete-workspace-layer) Workspace Layer
  - GET Workspace Layer [Thumbnail](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-layer-thumbnail)/[Style](doc/rest.md#get-workspace-layer-style)/[Metadata Comparison](doc/rest.md#get-workspace-layer-metadata-comparison)/[Chunk](doc/rest.md#get-workspace-layer-chunk)
  - [GET](doc/rest.md#get-workspace-map)/[PATCH](doc/rest.md#patch-workspace-map)/[DELETE](doc/rest.md#delete-workspace-map) Workspace Map
  - GET Workspace Map [File](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-map-file)/[Thumbnail](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-map-thumbnail)/[Metadata Comparison](doc/rest.md#get-workspace-map-metadata-comparison)
  - GET Workspace [Layers](doc/rest.md#get-workspace-layers)/[Maps](doc/rest.md#get-workspace-maps)
  - GET [Layers](doc/rest.md#get-layers)/[Maps](doc/rest.md#get-maps)/[Publications](doc/rest.md#get-publications)
  - DELETE Workspace [Layers](doc/rest.md#delete-workspace-layers)/[Maps](doc/rest.md#delete-workspace-maps)
  - requests to [WMS](doc/endpoints.md#web-map-service) and [WFS](doc/endpoints.md#web-feature-service) endpoints
- [#165](https://github.com/LayerManager/layman/issues/165) POST Workspace [Layers](doc/rest.md#post-workspace-layers)/[Maps](doc/rest.md#post-workspace-maps) respects roles in [GRANT_CREATE_PUBLIC_WORKSPACE](doc/env-settings.md#grant_create_public_workspace) and [GRANT_PUBLISH_IN_PUBLIC_WORKSPACE](doc/env-settings.md#grant_publish_in_public_workspace)
- [#165](https://github.com/LayerManager/layman/issues/165) Many endpoints return previously associated [role names](doc/models.md#role) in `access_rights.read` and `access_rights.write` keys:
  - [GET](doc/rest.md#get-workspace-layer)/[PATCH](doc/rest.md#patch-workspace-layer) Workspace Layer
  - [GET](doc/rest.md#get-workspace-map)/[PATCH](doc/rest.md#patch-workspace-map) Workspace Map
  - GET Workspace [Layers](doc/rest.md#get-workspace-layers)/[Maps](doc/rest.md#get-workspace-maps)
  - GET [Layers](doc/rest.md#get-layers)/[Maps](doc/rest.md#get-maps)/[Publications](doc/rest.md#get-publications)
- [#165](https://github.com/LayerManager/layman/issues/165) Name of [users](doc/models.md#username) and [public workspaces](doc/models.md#public-workspace) are from now on restricted to a maximum length of 59 characters.
- [940](https://github.com/LayerManager/layman/issues/940) Use `userId` as OAuth2 "sub" instead of `username`. This is suitable for Wagtail.
- [940](https://github.com/LayerManager/layman/issues/940) Stop supporting Liferay as OAuth2 provider.
- [941](https://github.com/LayerManager/layman/issues/941) Wagtail database is now persistent when restarting Layman or Wagtail.
- All changes from [v1.22.1](#v1221), [v1.22.2](#v1222) and [v1.22.3](#v1223).
- [#960](https://github.com/LayerManager/layman/issues/960) Handle WMS requests with HTTP error more efficiently in timgen.
- [#962](https://github.com/LayerManager/layman/issues/962) Make values of `layman_metadata.publication_status` and `status` key(s) more consistent in responses of PATCH Workspace [Layer](doc/rest.md#patch-workspace-layer)/[Map](doc/rest.md#patch-workspace-map) and GET Workspace [Layer](doc/rest.md#get-workspace-layer)/[Map](doc/rest.md#get-workspace-map).
- Timgen handles better some edge cases:
  - If map's [internal layer](doc/models.md#internal-map-layer) points to non-existent workspace, Timgen is faster and does not fail.
  - If map's file was not obtained from Layman, Timgen fails quickly.
- Upgrade Python dependencies
  - werkzeug 2.3.7 -> 3.0.7 (suggested by dependabot)
  - urllib3 1.26.16 -> 1.26.18 (suggested by dependabot)
  - pillow 10.0.0 -> 10.1.0 (suggested by dependabot)
  - cacheout 0.14.1 -> 0.15.0
  - flask 2.3.3 -> 3.0.0
  - jsonschema 4.19.0 -> 4.20.0
  - owslib 0.29.2 -> 0.29.3
  - importlib-metadata 6.8.0 -> 7.0.0
  - psycopg2-binary 2.9.7 -> 2.9.9
  - redis 5.0.0 -> 5.0.1
  - unidecode 1.3.6 -> 1.3.7
  - platformdirs 3.10.0 -> 4.1.0
  - pycodestyle 2.11.0 -> 2.11.1
  - pytest 7.4.2 -> 7.4.3
  - pytest-rerunfailures 12.0 -> 13.0
  - pytest-timeout 2.1.0 -> 2.2.0
- Add development dependency `plantuml/plantuml` for rendering PlantUML diagrams.

## v1.22.3
 2023-12-06
### Upgrade requirements
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.17.2
  ```
### Changes
- Improve logging in Layman Test Client related to Passport.js.
- [968](https://github.com/LayerManager/layman/issues/968) Enable to use not-so-secure SSL communication (UnsafeLegacyRenegotiation) in Layman Test Client. It can be activated by environment variable [NODE_OPTIONS](doc/env-settings.md#NODE_OPTIONS):
  ```
  NODE_OPTIONS="--openssl-config=/code/unsafe_openssl.cnf"
  ```

## v1.22.2
 2023-11-10
### Upgrade requirements
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.17.1
  ```
### Changes
- [#958](https://github.com/LayerManager/layman/issues/958) Fix `X-Forwarded-Proto` on LTC proxy with https protocol in demo environment.
- [#956](https://github.com/LayerManager/layman/issues/956) Fix login to GeoServer with https protocol.
- [#952](https://github.com/LayerManager/layman/issues/952) Fix patch saving publication files before access right validation.

## v1.22.1
 2023-10-12
### Changes
- [#949](https://github.com/LayerManager/layman/issues/949) Fix reading map-layer relations from map composition that includes also other than WMS and Vector layers.

## v1.22.0
 2023-10-05
### Upgrade requirements
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.17.0
  ```
- Stop using environment variable `LAYMAN_GS_PROXY_BASE_URL`, it has no effect to Layman anymore.
  - GeoServer's [Proxy Base URL](https://docs.geoserver.org/2.21.x/en/user/configuration/globalsettings.html) is now automatically set by Layman on each start. Value is automatically derived from environment variables [`LAYMAN_CLIENT_PUBLIC_URL`](doc/env-settings.md#layman_client_public_url) (protocol) and [`LAYMAN_PROXY_SERVER_NAME`](doc/env-settings.md#layman_proxy_server_name) (domain and port). URL path is always `/geoserver/`.
- Stop using environment variable `LAYMAN_GS_PATH`, it has no effect to Layman anymore.
  - GeoServer's URL path must be always `/geoserver/` (that is true for GeoServer shipped with Layman).
### Migrations and checks
#### Schema migrations
- [#868](https://github.com/LayerManager/layman/issues/868) Create new table `map_layer` in prime DB schema.
#### Data migrations
- [#887](https://github.com/LayerManager/layman/issues/887) Drop unique DB index on `users` table on `sub` column. Create unique DB index on `users` table on (`sub`, `issuer_id`) columns. 
- [#765](https://github.com/LayerManager/layman/issues/765) Fix `issuer_id` values in `users` table that were broken since v1.21.0.
- [#765](https://github.com/LayerManager/layman/issues/765) Remove `authn.txt` files from workspace directories. The same information as in `authn.txt` files is saved in prime DB schema.
- [#868](https://github.com/LayerManager/layman/issues/868) Fill table `map_layer` with relations between maps and [internal layers](doc/models.md#internal-map-layer) (layers published on this Layman instance). Relations to [external layers](doc/models.md#internal-map-layer) (layers of other servers) are not imported into the table.
### Changes
- [#868](https://github.com/LayerManager/layman/issues/868) Responses to many requests respect [HTTP X-Forwarded headers](doc/client-proxy.md#x-forwarded-http-headers) of the request. Those requests are:
  - GET [Publications](doc/rest.md#get-publications), [Layers](doc/rest.md#get-layers), [Workspace Layers](doc/rest.md#get-workspace-layers), [Maps](doc/rest.md#get-maps), and [Workspace Maps](doc/rest.md#get-workspace-maps)
  - [GET](doc/rest.md#get-workspace-layer), [PATCH](doc/rest.md#patch-workspace-layer), and [DELETE](doc/rest.md#delete-workspace-layer) Workspace Layer
  - [GET](doc/rest.md#get-workspace-map), [PATCH](doc/rest.md#patch-workspace-map), and [DELETE](doc/rest.md#delete-workspace-map) Workspace Map
  - [GET Workspace Map File](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-map-file)
  - [POST](doc/rest.md#post-workspace-layers) and [DELETE](doc/rest.md#delete-workspace-layers) Workspace Layers
  - [POST](doc/rest.md#post-workspace-maps) and [DELETE](doc/rest.md#delete-workspace-maps) Workspace Maps
  - requests to [WMS](doc/endpoints.md#web-map-service) and [WFS](doc/endpoints.md#web-feature-service) endpoints
- [#868](https://github.com/LayerManager/layman/issues/868) Responses to [GET Workspace Layer Metadata Comparison](doc/rest.md#get-workspace-layer-metadata-comparison) and [GET Workspace Map Metadata Comparison](doc/rest.md#get-workspace-map-metadata-comparison) do not respect [HTTP X-Forwarded headers](doc/client-proxy.md#x-forwarded-http-headers) of the request intentionally, in order to keep URLs in canonical form.
- [#868](https://github.com/LayerManager/layman/issues/868) Relations between map and [internal layers](doc/models.md#internal-map-layer) are updated in `map_layer` table when calling [POST Workspace Maps](doc/rest.md#post-workspace-maps), [PATCH Workspace Map](doc/rest.md#patch-workspace-map), [DELETE Workspace Map](doc/rest.md#delete-workspace-map), and [DELETE Workspace Maps](doc/rest.md#delete-workspace-maps).
- [#901](https://github.com/LayerManager/layman/issues/901) Endpoints [POST](doc/rest.md#post-workspace-maps) and [PATCH](doc/rest.md#patch-workspace-map) accept map compositions in version `3.x.x`.
- [#927](https://github.com/LayerManager/layman/issues/927) SLD styles are internally published to GeoServer with [`raw`](https://docs.geoserver.org/2.21.x/en/user/rest/api/styles.html#raw) parameter set to `True`.
- [#880](https://github.com/LayerManager/layman/issues/880) Use Docker Compose v2 (`docker compose`) in Makefile without `compatibility` flag and remove `Makefile_docker-compose_v1` file. Docker containers are named according to Docker Compose v2 and may have different name after upgrade.
- [#765](https://github.com/LayerManager/layman/issues/765) Stop saving OAuth2 claims in filesystem, use prime DB schema only.
- [#893](https://github.com/LayerManager/layman/issues/893) It is possible to specify logging level by new environment variable [LAYMAN_LOGLEVEL](doc/env-settings.md#LAYMAN_LOGLEVEL). Default level is `INFO`.
- Use `psycopg2.pool.ThreadedConnectionPool` to share DB connections.
- Add new test Python dependency:
  - jsonpath-ng 1.6.0
- Upgrade Python dependencies
  - certifi 2023.5.7 -> 2023.7.22 (suggested by dependabot)
  - tornado 6.3.2 -> 6.3.3 (suggested by dependabot)
  - flask 2.3.2 -> 2.3.3
  - jsonschema 4.17.3 -> 4.19.0
  - lxml 4.9.2 -> 4.9.3
  - owslib 0.28.1 -> 0.29.2
  - psycopg2-binary 2.9.5 -> 2.9.7
  - redis 4.5.5 -> 5.0.0
  - autopep8 2.0.1 -> 2.0.4
  - flake8 6.0.0 -> 6.1.0
  - pillow 9.3.0 -> 10.0.0
  - pycodestyle 2.10.0 -> 2.11.0 (to be consistent with GitHub Actions)
  - pytest 7.2.0 -> 7.4.2
  - pytest-rerunfailures 10.3 -> 12.0
  - watchdog 2.2.0 -> 3.0.0

## v1.21.1
 2023-07-21
### Migrations and checks
#### Data migrations
- [#887](https://github.com/LayerManager/layman/issues/887) Drop unique DB index on `users` table on (`sub`, `issuer_id`) columns. Create unique DB index on `users` table on `sub` column.
### Changes
- [#887](https://github.com/LayerManager/layman/issues/887) Fix creating new user workspaces for existing users that happened in v1.21.0.

## v1.21.0
 2023-07-06
### Upgrade requirements
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.16.0
  ```
- Rename environment variable `OAUTH2_LIFERAY_SECRET` to `OAUTH2_CLIENT_SECRET`.
- Rename all environment variables `OAUTH2_LIFERAY_SECRET<n>` to `OAUTH2_CLIENT<n>_SECRET`. For example, variable `OAUTH2_LIFERAY_SECRET4` becomes `OAUTH2_CLIENT4_SECRET`.
- Rename all other `OAUTH2_LIFERAY_<postfix>` environment variables to `OAUTH2_<postfix>`. For example, variable `OAUTH2_LIFERAY_AUTH_URL` becomes `OAUTH2_AUTH_URL`.
- If you are using environment variable [`OAUTH2_CALLBACK_URL`](doc/env-settings.md#oauth2_callback_url), change only its URL path from `/client/authn/oauth2-liferay/callback` to `/client/authn/oauth2-provider/callback`. Keep protocol, domain, and port unchanged.
- Stop using environment variable `LAYMAN_AUTHN_OAUTH2_PROVIDERS`, it has no effect to Layman anymore. There is exactly one OAuth2 provider Python module now, no need to set it.
- Stop using environment variable `FLASK_ENV`, it has no effect to Layman anymore.
  - If you used environment variable `FLASK_ENV` with value `development`, add new environment variable [`FLASK_DEBUG`](https://flask.palletsprojects.com/en/stable/config/?highlight=flask_debug#DEBUG):
    ```
    FLASK_DEBUG=1
    ```
- Stop using environment variable `CSW_RECORD_URL`, it has no effect to Layman anymore. Value is derived from variable `CSW_PROXY_URL`.
- Stop using HTTP header `AuthorizationIssUrl` when [authenticating by OAuth](doc/oauth2/index.md). The header has no effect to Layman anymore. There is exactly one OAuth2 provider now, no need to distinguish it. Now, the only distinguished HTTP header when authenticating by OAuth2 is `Authorization` header.
- If you are running Layman with development settings (e.g. starting it with `make start-dev`)
  - change values of environment variables:  
    ```
    OAUTH2_CLIENT_ID=VECGuQb00tWt8HZNkA4cxu6dnoQD5pF6Up3daAoK
    OAUTH2_CLIENT_SECRET=aY14rwkEKasNqBEZX8OnhpRk8lpHAfT7oKTlf4LriEK8oMZxhnGKcnt4bZ72pceNEl83B6LtBvhKr3BqBLFA80Pd6Ugav2rkc8bk7TE4LkaoB2qcBQmjiOiEpizsgZGx
    OAUTH2_AUTH_URL=http://localhost:8083/o/authorize
    OAUTH2_TOKEN_URL=http://wagtail:8000/o/token/
    OAUTH2_INTROSPECTION_URL=http://wagtail:8000/o/introspect/
    OAUTH2_INTROSPECTION_SUB_KEY=username
    OAUTH2_USER_PROFILE_URL=http://wagtail:8000/profile
    ```
  - unset environment variable `OAUTH2_SCOPE` (previously [`OAUTH2_LIFERAY_SCOPE`](https://github.com/LayerManager/layman/blob/v1.20.1/doc/env-settings.md#oauth2_liferay_scope))
  - after [usual dev upgrade commands](README.md#upgrade) run also
    ```
    make wagtail-build
    ```
- If your [upgrade command](README.md#upgrade) ends with message `Error response from daemon: invalid IP address in add-host: "host-gateway"`, try to uninstall Docker Engine completely and install it again with Docker Compose plugin (see e.g. manual for [Centos](https://docs.docker.com/engine/install/centos/)). Then run upgrade command again.
### Migrations and checks
#### Schema migrations
- [#528](https://github.com/LayerManager/layman/issues/528) Add new data type `enum_wfs_wms_status` and create new string column `wfs_wms_status` in `publications` table in prime DB schema.
#### Data migrations
- [#528](https://github.com/LayerManager/layman/issues/528) Fill column `wfs_wms_status` in `publications` table in prime DB schema. Set value `AVAILABLE` for each vector layer that is fully available in WFS and WMS and for each raster layer that is fully available in WMS. Set `NOT_AVAILABLE` for all other layers and `null` for all existing maps. 
- [#520](https://github.com/LayerManager/layman/issues/520) Set MetadataURL for each layer in WFS and WMS workspace in GeoServer.
### Changes
- [#769](https://github.com/LayerManager/layman/issues/769) New request [GET Publications](doc/rest.md#get-publications) was added. It enables querying both [layers](doc/models.md#layer) and [maps](doc/models.md#map) by single request. 
- [#769](https://github.com/LayerManager/layman/issues/769) New key `publication_type` was added to responses of requests [GET Publications](doc/rest.md#get-publications), [GET Layers](doc/rest.md#get-layers), [GET Workspace Layers](doc/rest.md#get-workspace-layers), [GET Maps](doc/rest.md#get-maps), and [GET Workspace Maps](doc/rest.md#get-workspace-maps). Possible values of the key are `layer` and `map`. 
- [#528](https://github.com/LayerManager/layman/issues/528) New key `wfs_wms_status` was added to layer items in responses of requests [GET Layers](doc/rest.md#get-layers), [GET Workspace Layers](doc/rest.md#get-workspace-layers), and [GET Publications](doc/rest.md#get-publications).
- [#520](https://github.com/LayerManager/layman/issues/520) New element `MetadataURL` was added for each layer to GetCapabilities response of WFS `2.0.0` and WMS `1.3.0`. The element contains URL of CSW metadata record of the layer.
- [#800](https://github.com/LayerManager/layman/issues/800) Requests [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) support new parameter `time_regex_format`. Its value is later accessible in the new subkey `wms`.`time`.`regex_format` in responses of [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) requests.
- [#764](https://github.com/LayerManager/layman/issues/764), [#860](https://github.com/LayerManager/layman/issues/860) Layman accepts new types of QML styles:
  - labels without symbology
  - point clustering
- [#857](https://github.com/LayerManager/layman/issues/857) Requests [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) accept `host.docker.internal` in `external_table_uri` parameter to reach `localhost` of host server.
- [#847](https://github.com/LayerManager/layman/issues/847) Fix publishing external table layers with `@` character or other dangerous characters in the username or in the password.
- [#833](https://github.com/LayerManager/layman/issues/833) Make Timgen WMS requests more robust (handle WMS errors, delayed retry, add timestamp to each request).
- [#877](https://github.com/LayerManager/layman/issues/877) Use Docker Compose v2 (`docker compose`) in Makefile. As of now, all containers are named in the same way as previously. Old Makefile using Docker Compose v1 (`docker-compose`) is archived as `Makefile_docker-compose_v1`. It will be removed in the next minor release.
- [#815](https://github.com/LayerManager/layman/issues/815) Propagate [`LAYMAN_PROXY_SERVER_NAME`](doc/env-settings.md#LAYMAN_PROXY_SERVER_NAME) value to GeoServer environment variable [GEOSERVER_CSRF_WHITELIST](https://docs.geoserver.org/latest/en/user/security/webadmin/csrf.html).
- [#765](https://github.com/LayerManager/layman/issues/765) Remove Liferay from dev stack, use [Wagtail CRX](https://docs.coderedcorp.com/wagtail-crx/) + [Django OAuth Toolkit](https://django-oauth-toolkit.readthedocs.io/en/latest/) as new OAuth2 provider (authorization server).
- Upgrade Python dependencies
  - flask 2.2.2 -> 2.3.2
  - redis 4.5.1 -> 4.5.4
  - owslib 0.27.2 -> 0.28.1
  - requests 2.28.1 -> 2.31.0
- Upgrade Node.js Timgen dependencies
  - vite 3.2.5 -> 3.2.7
- Document that temporal part of timeseries datetime dimension extracted by [`time_regex` parameter](doc/rest.md#post-workspace-layers) is cut off, so the smallest possible unit of datetime dimension is one day.

## v1.20.1
 2023-04-11
### Changes
- [#818](https://github.com/LayerManager/layman/issues/818) Fix publishing QML layer from external DB with geo-column name other than `wkb_geometry`.
- [#812](https://github.com/LayerManager/layman/issues/812) Fix processing of WFS-T queries with implicit namespace. 
- Fix `time_regex` sample values in documentation and tests.

## v1.20.0
 2023-03-01
### Upgrade requirements
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.15.0
  ```
### Migrations and checks
#### Schema migrations
- [#703](https://github.com/LayerManager/layman/issues/703) Create new json column `external_table_uri` in `publications` table in prime DB schema.
- [#703](https://github.com/LayerManager/layman/issues/703) Rename column `file_type` to `geodata_type` in `publications` table in prime DB schema.
#### Data migrations
- [#703](https://github.com/LayerManager/layman/issues/703) Fill column `external_table_uri` in `publications` table in prime DB schema. Value is set to `null` for all existing publications.
### Changes
- [#703](https://github.com/LayerManager/layman/issues/703) Endpoints [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) support new body parameter `external_table_uri`.
- [#703](https://github.com/LayerManager/layman/issues/703)  Endpoints [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) return new keys:
  - `original_data_source` with values `file` or `database_table`
  - `geodata_type` which replaces key `file.file_type` that is deprecated now
  - `db` which replaces key `db_table` that is deprecated now
- [#703](https://github.com/LayerManager/layman/issues/703) Attribute names in [WFS-T requests](doc/endpoints.md#web-feature-service) must match to regex `^[a-zA-Z_][a-zA-Z_0-9]*$`, otherwise Layman error is raised. It applies to attributes of both internal and external tables, and only to attributes that not exist in database yet.
- [#703](https://github.com/LayerManager/layman/issues/703) Endpoint [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) raises exception if parameter `crs` is used without `file` parameter. It's the same behaviour as behaviour of [POST Workspace Layers](doc/rest.md#post-workspace-layers) endpoint.
- [#772](https://github.com/LayerManager/layman/issues/772) Speed up endpoints [GET Workspace Layer Thumbnail](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-layer-thumbnail), [GET Workspace Layer Style](doc/rest.md#get-workspace-layer-style), [GET Workspace Map Thumbnail](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-map-thumbnail) and [GET Workspace Map File](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-map-file).
- [#755](https://github.com/LayerManager/layman/issues/755) Fix generation of some map thumbnails by downgrading Node.js of Timgen from v18 to v16.
- [#755](https://github.com/LayerManager/layman/issues/755) Change Node.js dependencies of Timgen:
  - http-server -> express 4
  - cors-anywhere -> http-proxy-middleware 2 

## v1.19.0
 2023-01-11
### Upgrade requirements
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.14.0
  ```
- If you are running Layman with development settings, run  
```
make build-dev
make timgen-build
make client-build
```
### Migrations and checks
#### Schema migrations
#### Data migrations
### Changes
- [#348](https://github.com/LayerManager/layman/issues/348) Upgrade GeoServer to 2.21.2.
  - [#613](https://github.com/LayerManager/layman/issues/613) Workspace-specific WMS GetCapabilities documents includes LegendURL element for every style of every layer. Previously vector layers with QML style did not have it. [GetLegendGraphic](doc/endpoints.md#getlegendgraphic) queries can be parametrized depending on layer style.
  - In workspace-specific WMS GetCapabilities documents, style name consists only of style name without `<workspace>:` prefix. For example, formerly it was `testuser_wms:blue_style`, now it is only `blues_style`.
  - [#681](https://github.com/LayerManager/layman/issues/681) Enable to publish layer with specific SLD style.
  - [#681](https://github.com/LayerManager/layman/issues/681) Endpoints [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) normalize grayscale float raster files with alpha channel to grayscale without it with internal mask 0/1.
  - Layman now uses official [GeoServer docker image](https://github.com/geoserver/docker) for demo and development purpose. 
- [#720](https://github.com/LayerManager/layman/issues/720) Upgrade Python dependencies
  - celery 5.0.5 -> 5.2.7
  - flask 2.0.2 -> 2.2.2
  - unidecode 1.3.2 -> 1.3.6
  - psycopg2-binary 2.9.3 -> 2.9.5
  - owslib 0.22.0 -> 0.27.2
  - requests 2.27.0 -> 2.28.1
  - jsonschema 4.3.3 -> 4.17.3
  - flower 1.0.0 -> 1.2.0
  - selenium 4.1.0 -> 4.7.2
  - cacheout 0.13.1 -> 0.14.1
  - kombu 5.2.3 -> 5.2.4
- [#720](https://github.com/LayerManager/layman/issues/720) Remove Python dependency "pyproj".
- [#720](https://github.com/LayerManager/layman/issues/720) Upgrade Python dev dependencies
  - pytest 6.2.5 -> 7.2.0
  - watchdog 2.1.6 -> 2.2.0
  - flake8 4.0.1 -> 6.0.0
  - pycodestyle 2.8.0 -> 2.10.0
  - pylint 2.7.4 -> 2.15.9
  - autopep8 1.6.0 -> 2.0.1
  - pytest-rerunfailures 10.2 -> 10.3
  - pytest-timeout 2.0.2 -> 2.1.0
- [#726](https://github.com/LayerManager/layman/issues/726) Upgrade Node.js of Laymen Test Client from v12 to v18 and dependencies:
  - connect-redis 3 -> 6
  - dotenv 8 -> 16
  - http-proxy-middleware 0.21 -> 2
  - isomorphic-unfetch 2 -> 3
  - next 9 -> 13
  - react 16 -> 18
  - react-dom 16 -> 18
  - redis 3 -> 4
  - semantic-ui-react 0.88 -> 2
  - xml-formatter 2 -> 3
- [#732](https://github.com/LayerManager/layman/issues/732) Upgrade Node.js of Timgen from v10 to v18 and dependencies:
  - ol 5 -> 7
  - http-server 0.11 -> 14
- [#732](https://github.com/LayerManager/layman/issues/732) Use "vite" instead of "parcel" and "babel" for dev & build of Timgen.

## v1.18.0
 2022-11-22
### Upgrade requirements
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.13.0
  ```
### Migrations and checks
#### Schema migrations
- [#635](https://github.com/LayerManager/layman/issues/635) Create new boolean column `image_mosaic` in `publication` table.
#### Data migrations
- [#635](https://github.com/LayerManager/layman/issues/635) Fill column `image_mosaic` in `publications` table in prime DB schema for all publications. Value of each publication is set to `false`.
### Changes
- [#635](https://github.com/LayerManager/layman/issues/635) Endpoints [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) support publishing [timeseries](doc/models.md#timeseries) raster layers. Temporal information is read from file names using new body parameter *time_regex*. Timeseries data files keep their original slugified names in both Layman and GeoServer data directories (instead of renaming to `<layer_name>.<extension>`). Each timeseries is published to GeoServer as one ImageMosaic coverage store.
- [#446](https://github.com/LayerManager/layman/issues/446) If endpoint [POST Workspace Layers](doc/rest.md#post-workspace-layers) receives grayscale input raster file (with or without alpha band) and if no input style was sent with the raster file, then Layman will automatically create and use customized SLD style to stabilize contrast of the layer in WMS.
- [#446](https://github.com/LayerManager/layman/issues/446) Transparency of paletted GeoTIFF with transparent data values is respected in WMS. No custom style is needed. It was probably fixed in [v1.16.0](#v1160) by upgrade of GeoServer.
- [#635](https://github.com/LayerManager/layman/issues/635) Endpoints [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) returns new subkeys:
  - `file.paths` with list of paths to all main data files
  - `image_mosaic` for raster layers stating that layer was published to GeoServer using ImageMosaic coverage store  (`true` value for [timeseries](doc/models.md#timeseries) and `false` otherwise)
  - `wms.time` for [timeseries](doc/models.md#timeseries) with list of available time instants and regular expression used to extract them from file names
- [#635](https://github.com/LayerManager/layman/issues/635) Subkey `file.path` is marked deprecated for endpoints [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer). Use `file.paths` instead.
- [#635](https://github.com/LayerManager/layman/issues/635) Metadata sources returns new key ['temporal_extent'](doc/metadata.md#temporal_extent).
- [#635](https://github.com/LayerManager/layman/issues/635) Endpoints [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) do not support combination of zip file and uncompressed main file. 
- [#697](https://github.com/LayerManager/layman/issues/697) Normalized GeoTIFF files are created as BigTIFF to enable publishing raster files greater than 4 GB.
- [#660](https://github.com/LayerManager/layman/issues/660) Vector data files with invalid byte sequence (e.g. ShapeFile with invalid byte sequence in UTF-8 encoding) are first converted to GeoJSON, then cleaned with iconv, and finally imported to database.
- [#667](https://github.com/LayerManager/layman/issues/667) Fix broken statistics during normalization of float rasters with big nodata value.
- [#668](https://github.com/LayerManager/layman/issues/668) Fix broken size of raster in EPSG:3034 during normalization.
- [#669](https://github.com/LayerManager/layman/issues/669) Fix slow publication of vector layers metadata to Micka. The reason was slow guessing of [`spatial_resolution.scale_denominator`](doc/metadata.md#spatial_resolution) metadata property.
- [#701](https://github.com/LayerManager/layman/pull/701) After publishing to GeoServer, Layman checks that Layer is available in WMS & WFS GetCapabilities to prevent situation when GeoServer hides publishing error. It may happen when data file with wrong CRS is published.

## v1.17.0
 2022-07-21
### Upgrade requirements
- Only versions 1.14.0 and newer can be upgraded to this version. For older versions, please upgrade to last 1.16.x first.
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.12.0
  ```
### Migrations and checks
#### Schema migrations
- [#576](https://github.com/LayerManager/layman/issues/576) Create new column `file_type` in `publications` table.
- [#541](https://github.com/LayerManager/layman/issues/541) Rename vector data DB tables to `layer_<uuid>` format.
#### Data migrations
- [#576](https://github.com/LayerManager/layman/issues/576) Fill column `file_type` in `publications` table in prime DB schema for all publications. Value of each map will be `NULL`. Value of each layer will be same as value of `file.file_type` in [GET Workspace Layer](doc/rest.md#get-workspace-layer) response (i.e. `vector`, `raster`, or `unknown`).
### Changes
- [#551](https://github.com/LayerManager/layman/issues/551) Endpoints [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) support new body parameter *overview_resampling*.
- [#576](https://github.com/LayerManager/layman/issues/576) Endpoints [GET Layers](doc/rest.md#get-layers) and [GET Workspace Layers](doc/rest.md#get-workspace-layers) returns new `file.file_type` key with the same value as `file.file_type` in [GET Workspace Layer](doc/rest.md#get-workspace-layer) response (i.e. `vector`, `raster`, or `unknown`).
- [#541](https://github.com/LayerManager/layman/issues/541) Layer name and map name can start with numbers.
- Maximum length of layer and map name is 210 characters.
- [#606](https://github.com/LayerManager/layman/issues/606) Fix filtering and ordering publications by bounding box in case of publication with whole world bounding box in database.
- New environment variable [OAUTH2_LIFERAY_SCOPE](https://github.com/LayerManager/layman/blob/v1.20.1/doc/env-settings.md#oauth2_liferay_scope). Introduced in v1.16.2.
- New environment variable [OAUTH2_LIFERAY_INTROSPECTION_SUB_KEY](https://github.com/LayerManager/layman/blob/v1.22.3/doc/env-settings.md#oauth2_introspection_sub_key). Introduced in v1.16.1.
- [#599](https://github.com/LayerManager/layman/issues/599) Layman supports uploading data files with upper or mixed case extensions. Introduced in v1.16.1.
- [#541](https://github.com/LayerManager/layman/issues/541) Vector layers are stored in DB table with name in form `layer_<UUID>`, e.g. `layer_96b918c6_d88c_42d8_b999_f3992b826958`, previously the name of the table was the same as name of the layer.

## v1.16.3
 2022-06-20
### Changes
- Stop Firefox instances if map thumbnail generation times out. Previously Firefox processes keeps running and were never stopped.
- Add logging for Micka response in case of exception.

## v1.16.2
 2022-03-07
### Upgrade requirements
- Change environment variable [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION):
  ```
  LAYMAN_CLIENT_VERSION=v1.11.0
  ```
- If you are using Liferay as OAuth2 provider, set new environment variable [OAUTH2_LIFERAY_SCOPE](https://github.com/LayerManager/layman/blob/v1.20.1/doc/env-settings.md#oauth2_liferay_scope):
  ```
  OAUTH2_LIFERAY_SCOPE=liferay-json-web-services.everything.read.userprofile
  ```
  If you are using Wagtail, do not set this variable at all (not even to empty string).
- If you are running Layman with development settings, run  
  ```
  make client-build
  ```
### Changes
- New environment variable [OAUTH2_LIFERAY_SCOPE](https://github.com/LayerManager/layman/blob/v1.20.1/doc/env-settings.md#oauth2_liferay_scope).

## v1.16.1
 2022-02-25
### Changes
- Fix infinity loop when generating map thumbnail. One of consequences was that such infinity loops consumed all celery workers and it was not possible to complete POST/PATCH map or layer.
- Fix empty map thumbnail. In some cases, map thumbnail was generated as if anonymous user asks for the map. Now the thumbnail is generated as if user with writing rights asks for the map.
- New environment variable [OAUTH2_LIFERAY_INTROSPECTION_SUB_KEY](https://github.com/LayerManager/layman/blob/v1.22.3/doc/env-settings.md#oauth2_introspection_sub_key).
- [#599](https://github.com/LayerManager/layman/issues/599) Layman supports uploading data files with upper or mixed case extensions.

## v1.16.0
 2022-02-18
### Upgrade requirements
- Only versions 1.12.0 and newer can be upgraded to this version. For older versions, please upgrade to last 1.15.x first.
- Due to GeoServer upgrade, it's possible that `make upgrade-demo` fails with following error:
```shell
Waiting for GeoServer REST API, user=layman, url=http://geoserver:8080/geoserver/rest/workspaces/
Traceback (most recent call last):
  File "src/wait_for_deps.py", line 158, in <module>
    main()
  File "src/wait_for_deps.py", line 88, in main
    response.raise_for_status()
  File "/usr/local/lib/python3.8/dist-packages/requests/models.py", line 960, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 401 Client Error:  for url: http://geoserver:8080/geoserver/rest/workspaces/
```
If you encounter such error, you can use script `upgrade_v1_16_fix_gs.sh` for fixing this issue. Be aware, that you will lose some security GeoServer settings, like Layman user and admin password, so you need to set them again after. The script needs to be run from Layman`s root directory:
```shell
make stop-demo
sh src/layman/upgrade/upgrade_v1_16_fix_gs.sh
```
After the script finishes, either set [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) or create [LAYMAN_GS_USER](doc/env-settings.md#LAYMAN_GS_USER) in GeoServer GUI.
- Set new environment variable [LAYMAN_INPUT_SRS_LIST](doc/env-settings.md#LAYMAN_INPUT_SRS_LIST)
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.10.0`
- Unset environment variable [LAYMAN_SETTINGS_MODULE](https://github.com/LayerManager/layman/blob/v1.15.0/doc/env-settings.md), it has no effect anymore.
- If you are running Layman with development settings, run  
```
make geoserver-build
make timgen-build
make client-build
```
### Migrations and checks
#### Schema migrations
- [#64](https://github.com/LayerManager/layman/issues/64) Create new column `srid` in `publications` table.
#### Data migrations
- [#64](https://github.com/LayerManager/layman/issues/64) Native CRS of previously uploaded layers is set to `EPSG:3857`.
- [#64](https://github.com/LayerManager/layman/issues/64) Native CRS of previously uploaded maps is set according their composition file (either `EPSG:3857` or `EPSG:4326`) and their composition file is upgraded to [version 2.0.0](https://raw.githubusercontent.com/hslayers/map-compositions/2.0.0/schema.json).
### Changes
- [#64](https://github.com/LayerManager/layman/issues/64) Upgrade GeoServer to 2.15.2, because 2.13.0 had serious problem with transformations of EPSG:5514.
- [#64](https://github.com/LayerManager/layman/issues/64) Responses of [GET Layers](doc/rest.md#get-layers), [GET Workspace Layers](doc/rest.md#get-workspace-layers), [GET Workspace Layer](doc/rest.md#get-workspace-layer), [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer), [GET Maps](doc/rest.md#get-maps), [GET Workspace Maps](doc/rest.md#get-workspace-maps), [GET Workspace Map](doc/rest.md#get-workspace-map), [PATCH Workspace Map](doc/rest.md#patch-workspace-map) contains new attributes
   - `native_crs` with native CRS in form "EPSG:&lt;code&gt;", e.g. "EPSG:4326"
   - `native_bounding_box` with coordinates in native CRS [minx, miny, maxx, maxy]
- [#64](https://github.com/LayerManager/layman/issues/64) New environment variable [LAYMAN_INPUT_SRS_LIST](doc/env-settings.md#LAYMAN_INPUT_SRS_LIST)
- [#64](https://github.com/LayerManager/layman/issues/64) Layman supports import of layers in EPSG:3034, EPSG:3035, EPSG:5514, EPSG:32633, EPSG:32634 and EPSG:3059.
- [#64](https://github.com/LayerManager/layman/issues/64) New raster layers are normalized in native CRS. New vector layers are imported into DB also in native CRS. Existing layers (normalized raster files, vector tables in DB) are kept in `EPSG:3857` until they are patched with another file, or deleted.
- [#519](https://github.com/LayerManager/layman/issues/64) Endpoints [GET Layers](doc/rest.md#get-layers), [GET Workspace Layers](doc/rest.md#get-workspace-layers), [GET Maps](doc/rest.md#get-maps), [GET Workspace Maps](doc/rest.md#get-workspace-maps) support new query parameters *bbox_filter_crs* and *ordering_bbox_crs*.
- [#64](https://github.com/LayerManager/layman/issues/64) Layer thumbnails are generated in native CRS of the layer.
- [#64](https://github.com/LayerManager/layman/issues/64) WMS proxy was added to [WMS endpoint](doc/endpoints.md#web-map-service). In case of some special WMS GetMap requests, it changes requested CRS to fix some GeoServer issues.
- [#64](https://github.com/LayerManager/layman/issues/64) For layers in `EPSG:5514` and WFS requests in `CRS:84`, the features may have wrong coordinates by hundreds of meters. For requests in `EPSG:4326`, coordinates are correct.
- [#572](https://github.com/LayerManager/layman/issues/572) Endpoints [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) accept also raster files with `.jpeg` extension .
- [#64](https://github.com/LayerManager/layman/issues/64) Map compositions are validated against [map-composition-schema](https://github.com/hslayers/map-compositions) defined in `describedBy` key of map composition data JSON. Layman now supports only map compositions in version 2.
- [#489](https://github.com/LayerManager/layman/issues/489) Error responses from Micka and GeoServer are logged into log and also propagated as part of raised exception, so they can be seen from flower.
- [#548](https://github.com/LayerManager/layman/pull/548) Suppress GeoServer HTTP error 409 when setting layer access rights if they already have the same value.
- [#548](https://github.com/LayerManager/layman/pull/548) If Micka returns HTTP error 500 on CSW/SOAP Insert/Update/Delete, retry the request.
- [#548](https://github.com/LayerManager/layman/pull/548) If GeoServer returns HTTP error 500 on GetCapabilities, retry the request.
- Remove [LAYMAN_SETTINGS_MODULE](https://github.com/LayerManager/layman/blob/v1.15.0/doc/env-settings.md), import [`src/layman_settings.py`](src/layman_settings.py) directly.
- [#555](https://github.com/LayerManager/layman/pull/555) Upgrade Selenium from 3 to 4
- [#555](https://github.com/LayerManager/layman/pull/555) Use Firefox instead of Chrome in Selenium for map thumbnail generation and Layman Test Client tests.

## v1.15.1
 2021-12-06
### Changes
- [#525](https://github.com/LayerManager/layman/issues/525) Keep NoData value in normalized raster files. Also NoData values are normalized as transparent always, even if Alpha channel is available.

## v1.15.0
 2021-11-18
### Changes
- [#169](https://github.com/LayerManager/layman/issues/169) [POST Workspace Layers](doc/rest.md#post-workspace-layers) accepts also compressed data files in ZIP format (`*.zip`) in `file` parameter. [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) accepts also data file in ZIP format (`*.zip`) in `file` parameter. ZIP archives can be also uploaded by chunks.
- [#503](https://github.com/LayerManager/layman/issues/503) Raster data (e.g. GeoTIFF, JPEG2000, PNG, JPEG) sent on [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) are compressed during normalization to decrease occupied disk space.
- [#232](https://github.com/LayerManager/layman/issues/232) Prefixes '>=' or '==' can be used in [MICKA_ACCEPTED_VERSION](doc/env-settings.md#micka_accepted_version) environment variable.
- Documentation describes how to use external images in QML styles in [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) requests; see `style` parameter.
- [#169](https://github.com/LayerManager/layman/issues/169) [GET Workspace Layer](doc/rest.md#get-workspace-layer) returns path to main file inside archive if zipped file was sent (key `file.path`).
- [#465](https://github.com/LayerManager/layman/issues/465) Fix situation, when Layman does not start if *.qgis file of the first layer with QML style does not exist. It was already fixed in v1.14.1.
- [#464](https://github.com/LayerManager/layman/issues/464) Fix publishing layers with unusual attribute  names (e.g. `x,` or `Číslo`) and QML styles. It was already fixed in v1.14.1.
- [#459](https://github.com/LayerManager/layman/issues/459) Fix situation, when sometimes publication stayed in PENDING status after failure. It was already fixed in v1.14.1.
- [#502](https://github.com/LayerManager/layman/issues/502) Fix error message, when invalid raster file is sent.
- Fix: Layers, which were created in Layman, but not published in GeoServer due to any validation/error can now be patched. Previously internal error was raised for every [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) call.
- Rename item `username` to `workspace` in error 41.
- Detailed [test-related documentation for developers](tests/README.md).
- [#487](https://github.com/LayerManager/layman/issues/487) Upgrade
  - flask from 2.0 to 2.0.2+
  - celery from 4.4.7 to 5.0.5
  - kombu from 4.6.10 to 5.1.0
  - flower from 0.9.7 to 1.0.0
  - jsonschema from 3.2.0 to 4.0.1
  - psycopg2-binary from 2.8.6 to 2.9.1
  - requests from 2.25.1 to 2.26.0
  - unidecode from 1.2.0 to 1.3.2

## v1.14.1
 2021-09-14
### Changes
- [#465](https://github.com/LayerManager/layman/issues/465) Fix situation, when Layman does not start if *.qgis file of the first layer with QML style does not exist.
- [#464](https://github.com/LayerManager/layman/issues/464) Fix publishing layers with unusual attribute names (e.g. `x,` or `Číslo`) and QML styles.
- [#459](https://github.com/LayerManager/layman/issues/459) Fix situation, when sometimes publication stayed in PENDING status after failure

## v1.14.0
 2021-09-08
### Upgrade requirements
- It's strongly recommended to backup data directories, especially `deps/postgresql/data`, because of database upgrade.
- After [stopping layman and backing up data directories](README.md#upgrade), you need to migrate PostgreSQL data directory from v10 to v13. We created script that automatically migrates two databases:
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
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.9.0`
- Set new environment variables
  - [LAYMAN_GS_NORMALIZED_RASTER_DIRECTORY](doc/env-settings.md#LAYMAN_GS_NORMALIZED_RASTER_DIRECTORY)=normalized_raster_data
    - If you are running Layman with development settings, set value to `normalized_raster_data_dev` instead
  - [DEFAULT_CONNECTION_TIMEOUT](doc/env-settings.md#DEFAULT_CONNECTION_TIMEOUT)=10
- If you are running Layman with development settings, run  
```
make build-dev
make client-build
make timgen-build
```
### Migrations and checks
#### Data migrations
- All bounding boxes are cropped not to exceed extent of EPSG:3857 projection ([-20026376.39, -20048966.10, 20026376.39, 20048966.10]) in all sources except filesystem and DB table. Only bounding boxes are affected, not data itself.
### Changes
- [#167](https://github.com/LayerManager/layman/issues/167) Allow publishing also raster geospatial data using [POST Workspace Layers](doc/rest.md#post-workspace-layers) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer).
  - Following formats are supported:
     - [GeoTIFF](https://gdal.org/en/stable/drivers/raster/gtiff.html) 
     - [JPEG2000](https://gdal.org/en/stable/drivers/raster/jp2openjpeg.html)
     - [PNG](https://gdal.org/en/stable/drivers/raster/png.html)
     - [JPEG](https://gdal.org/en/stable/drivers/raster/jpeg.html)
  - Following input combinations of bands and color interpretations are supported:
    - 1 band: Gray
    - 1 band: Palette
      - Transparency will be ignored. See [#466](https://github.com/LayerManager/layman/issues/446) for details.
    - 2 bands: Gray, Alpha
      - Float data type with min/max values other than 0/255 may result in unexpected WMS output. See [#466](https://github.com/LayerManager/layman/issues/446) for details.
    - 3 bands: Red, Green, Blue
    - 4 bands: Red, Green, Blue, Alpha
  - Following input CRS are supported:
    - EPSG:3857
    - EPSG:4326
  - Published raster files are normalized before registering to GeoServer. Normalization includes conversion to GeoTIFF in EPSG:3857 with overviews (pyramids). NoData values are normalized as transparent only if Alpha band is not available and NoData is set for each band. Normalized rasters are stored in `normalized_raster_data` directory inside [LAYMAN_DATA_DIR](doc/env-settings.md#LAYMAN_DATA_DIR). Normalized GeoTiff is then published as new layer (coverage) on GeoServer. 
  - Raster layers are not stored in DB table. WFS is not available for raster layers. [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) do not return items `wfs` and `db_table` for raster layers.
  - Calling [WFS-T](doc/endpoints.md#web-feature-service) endpoint starts [asynchronous tasks](doc/async-tasks.md) only for vector layers.
- [#167](https://github.com/LayerManager/layman/issues/167) Add `file_type` item to `file` item in [GET Workspace Layer](doc/rest.md#get-workspace-layer) response to distinguish raster and vector layers.
- [#167](https://github.com/LayerManager/layman/issues/167) Metadata property `scale_denominator` was removed. Its value is now accessible as subproperty of new [`spatial_resolution`](doc/metadata.md#spatial_resolution) metadata property. The new metadata property `spatial_resolution` has one of two subproperties:
  - `scale_denominator` used for vector data
  - `ground_sample_distance` used for raster data
- [#367](https://github.com/LayerManager/layman/issues/367) When publishing or patching layer or map, it's bounding box is limited to extent of EPSG:3857 projection in all sources except filesystem and DB table. Only bounding box is affected, not data itself.
- [#347](https://github.com/LayerManager/layman/issues/347) When ordering publications by title, only letters, numbers, and spaces are considered.
- [#382](https://github.com/LayerManager/layman/pull/382) [Map composition schema](https://raw.githubusercontent.com/LayerManager/layman/v1.15.1/src/layman/map/schema.draft-07.json) allows new properties `hs.format.externalWFS` and `workspace`. It was already introduced in v1.13.1.
- [#385](https://github.com/LayerManager/layman/pull/385) The `style` property can be specified using a string in SLD format, URL to SLD file or JSON object. It was already introduced in v1.13.1.
- Errors `19`: 'Layer is already in process.' and `29`: 'Map is already in process.' are merged into `49`: 'Publication is already in process.'.
- Fix: In case of synchronous error during [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer) layer data on the server remains always untouched. Previously, layer data on the server could be lost.
- Fix: Raise error when more than one main layer file is sent in [POST Workspace Layers](doc/rest.md#post-workspace-layers) or [PATCH Workspace Layer](doc/rest.md#patch-workspace-layer).
- Fix [#408](https://github.com/LayerManager/layman/issues/408): Skip non-WMS layers in thumbnail generation. Previously thumbnail generation failed.
- [#418](https://github.com/LayerManager/layman/issues/418) Combination of none geometry type in layer file and any geometry type in QML file is allowed from now.
- [#380](https://github.com/LayerManager/layman/issues/380) Enable to upload geojson with "id" attribute with non-unique values.
- [#383](https://github.com/LayerManager/layman/issues/383) Add new Makefile target `upgrade-after-timeout` to finish upgrade in case of GeoServer call timeout.
- Fix [GET Workspace Layer](doc/rest.md#get-workspace-layer) documentation; `style` item was incorrectly used instead of `sld`.
- [#347](https://github.com/LayerManager/layman/issues/347) Upgrade PostgreSQL 10 to 13.3 and PostGIS 2.4 to 3.1. Use docker image from [layermanager/postgis@hub.docker.com](https://hub.docker.com/r/layermanager/postgis), source is located at [layermanager/docker-postgis@github.com](https://github.com/LayerManager/docker-postgis).
- [#367](https://github.com/LayerManager/layman/issues/367) Upgrade gdal from 2.4 to 3.3. Use docker image from [osgeo/gdal@hub.docker.com](https://hub.docker.com/r/osgeo/gdal), source is located at [osgeo/gdal@github.com](https://github.com/OSGeo/gdal/tree/master/docker).
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

## v1.13.2
 2021-06-25
### Changes
- Fix [#405](https://github.com/LayerManager/layman/issues/405). In some specific situations, [GET Workspace Layer](doc/rest.md#get-workspace-layer) and [GET Workspace Map](doc/rest.md#get-workspace-map) returned PENDING state although asynchronous tasks were already finished. Also PATCH request to these publications was not possible. It's fixed now.

## v1.13.1
 2021-06-07
### Changes
- [Map composition schema](https://raw.githubusercontent.com/LayerManager/layman/v1.15.1/src/layman/map/schema.draft-07.json) allows new properties `hs.format.externalWFS` and `workspace` ([#382](https://github.com/LayerManager/layman/pull/382)). The `style` property can be specified using a string in SLD format, URL to SLD file or JSON object ([#385](https://github.com/LayerManager/layman/pull/385)).

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
     - thumbnail is updated in filesystem and it is accessible using [GET Workspace Layer Thumbnail](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-layer-thumbnail)
  - update of thumbnail of each [map](doc/models.md#map) that points to at least one edited layer (thumbnail is updated in filesystem and accessible using [GET Workspace Map Thumbnail](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-map-thumbnail))  
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
    - Treat attribute names in QML (also known as '[launder](https://gdal.org/en/stable/drivers/vector/pg.html#layer-creation-options)').
    - New docker container with QGIS server called `qgis` in demo configuration.
    - New directory [LAYMAN_QGIS_DATA_DIR](doc/env-settings.md#LAYMAN_QGIS_DATA_DIR) is used to store [layer QGS files](doc/data-storage.md#filesystem).
    - [WMS](doc/endpoints.md#web-map-service) is moved to dedicated [GeoServer workspace](doc/data-storage.md#geoserver) whose name is composed from Layman's [workspace](doc/models.md#workspace) name and suffix `_wms`. [WFS](doc/endpoints.md#web-feature-service) remains in GeoServer workspace whose name is equal to Layman's workspace name.
    - Layers with [QGIS style](https://docs.qgis.org/3.40/en/docs/user_manual/style_library/style_manager.html#exporting-items) are published on [GeoServer dedicated WMS workspace](doc/data-storage.md#geoserver) through WMS cascade from QGIS server, where they are stored as QGS file. All layers are published directly from PostgreSQL database to GeoServer for [WFS workspace](doc/data-storage.md#geoserver).
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

  During startup, Layman passes definitions of each EPSG to GeoServer, either from its internal sources, or from [epsg.io](https://epsg.io/). If download from epsg.io fails, warning `Not able to download EPSG definition from epsg.io` appears in log. In such case, you can [set EPSG definition manually](https://docs.geoserver.org/2.21.x/en/user/configuration/crshandling/customcrs.html) and restart GeoServer.

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
- The fix of [#200](https://github.com/LayerManager/layman/issues/200) affects only newly posted or patched layers. To fix access rights on existing layers, you can either wait for 1.9 release (2021-01-15), or manually add ROLE_AUTHENTICATED for every [layer security rule](https://docs.geoserver.org/2.21.x/en/user/security/layer.html) which already contains ROLE_ANONYMOUS.
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
    - Security rules on GeoServer on [workspace level (workspace.*.r/w)](https://docs.geoserver.org/2.21.x/en/user/security/layer.html) are deleted and replaced with security rules on [layer level (workspace.layername.r/w)](https://docs.geoserver.org/2.21.x/en/user/security/layer.html) according to rules on Layman side.
- [#28](https://github.com/LayerManager/layman/issues/28) Only publications with [read access](doc/security.md#publication-access-rights) for EVERYONE are published to Micka as public.
- [#28](https://github.com/LayerManager/layman/issues/28) New REST endpoint [GET Users](doc/rest.md#get-users) with list of all users registered in Layman. This new endpoint was added to Test Client into tab "Others".
- [#28](https://github.com/LayerManager/layman/issues/28) [WMS endpoint](doc/endpoints.md#web-map-service) accepts same [authentication](doc/security.md#authentication) credentials (e.g. [OAuth2 headers](doc/oauth2/index.md#request-layman-rest-api)) as Layman REST API endpoints. It's implemented using Layman's WFS proxy. This proxy authenticates the user and send user identification to GeoServer.
- [#161](https://github.com/LayerManager/layman/issues/161) New method DELETE was implemented for endpoints [DELETE Workspace Maps](doc/rest.md#delete-workspace-maps) and [DELETE Workspace Layers](doc/rest.md#delete-workspace-layers).
- [#178](https://github.com/LayerManager/layman/issues/178) New attribute `screen_name` is part of response for [GET Users](doc/rest.md#get-users) and [Get Current User](doc/rest.md#get-current-user).
- [#178](https://github.com/LayerManager/layman/issues/178) LifeRay attribute `screen_name` is preferred for creating username in Layman. Previously it was first part of email.
- Attribute `groups` is no longer returned in [GET Workspace Map File](https://github.com/LayerManager/layman/blob/v2.1.0/doc/rest.md#get-workspace-map-file) response.
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
- [#65](https://github.com/LayerManager/layman/issues/65) Layman automatically setup [HTTP authentication attribute](https://docs.geoserver.org/2.21.x/en/user/security/tutorials/httpheaderproxy/index.html) and chain filter at startup. Secret value of this attribute can be changed in [LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE](doc/env-settings.md#LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE) and is used by Layman's WFS proxy.

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
- [#69](https://github.com/LayerManager/layman/issues/69) If you are running Layman with development or test settings, set [LAYMAN_SETTINGS_MODULE](https://github.com/LayerManager/layman/blob/v1.6.0/doc/env-settings.md) in your `.env` file to `layman_settings`. No action is required if you are running Layman based on demo settings (probably all production instances).
### Changes
- [#74](https://github.com/LayerManager/layman/issues/74) Layman user and role at GeoServer defined by [LAYMAN_GS_USER](doc/env-settings.md#LAYMAN_GS_USER) and [LAYMAN_GS_ROLE](doc/env-settings.md#LAYMAN_GS_ROLE) are now created automatically on Layman's startup if an only if new environment variable [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) is provided. There is no need to set [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) for other reason than automatically creating Layman user and Layman role.
   - No change is required. If you are migrating existing instance, Layman user and role are already created, so you don't need to set [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD). If this is your first Layman release, [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) is set in `.env` files starting with this version, so Layman user and role at GeoServer will be automatically created on startup.
   - No need to run command `make geoserver-reset-default-datadir` from now on. This command was removed from make options.
- [#62](https://github.com/LayerManager/layman/issues/62) GeoServer [Proxy Base URL](https://docs.geoserver.org/2.21.x/en/user/configuration/globalsettings.html) is now automatically set on Layman's startup according to [LAYMAN_GS_PROXY_BASE_URL](https://github.com/LayerManager/layman/blob/v1.21.1/doc/env-settings.md#LAYMAN_GS_PROXY_BASE_URL). If you do not set the variable, value is calculated as [LAYMAN_CLIENT_PUBLIC_URL](doc/env-settings.md#LAYMAN_CLIENT_PUBLIC_URL)+[LAYMAN_GS_PATH](https://github.com/LayerManager/layman/blob/v1.21.1/doc/env-settings.md#LAYMAN_GS_PATH). If you set it to empty string, no change of Proxy Base URL will be done on GeoServer side.
- [#83](https://github.com/LayerManager/layman/issues/89) All layers are created as `GEOMETRY` type, so any other type can be added (for example polygons can be added to points).
- [#73](https://github.com/LayerManager/layman/issues/73) Layman users are automatically created on GeoServer (either at start up of Layman or when reserved) with separate role and workspace. Username is the same as in Layman, name of role is `"USER_"+username`, name of workspace is the same as username. Read and write permissions for workspace are set according to Layman's authorization (as of now read-everyone-write-everyone or read-everyone-write-owner).
- New environment variables [LAYMAN_GS_USER_GROUP_SERVICE](doc/env-settings.md#LAYMAN_GS_USER_GROUP_SERVICE) and [LAYMAN_GS_ROLE_SERVICE](https://github.com/LayerManager/layman/blob/v1.22.0/doc/env-settings.md#LAYMAN_GS_ROLE_SERVICE) enable to control which user/group and role services are used at GeoServer. Not setting these variables means to use default services. 
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
  - [`scale_denominator`](doc/metadata.md#spatial_resolution) of Layer using distanced between vertices
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
