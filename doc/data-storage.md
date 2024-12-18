# Data Storage

Layman stores several types of data in several stores.

Types of data:
- [Users](#users)
- [Layers](#layers)
- [Maps](#maps)
- [Tasks](#tasks) (asynchronous tasks)
- [Data version](#data-version)

Data stores:
- [Redis](#redis)
- [Filesystem](#filesystem)
- [PostgreSQL](#postgresql)
- [GeoServer](#geoserver)

## Types of Data

### Users
Information about users includes their names, contacts, and authentication credentials.

When user [reserves his username](rest.md#patch-current-user), names, contacts and other relevant metadata are [obtained from authorization provider](oauth2/index.md#fetch-user-related-metadata) and saved to [Redis](#redis), [PostgreSQL](#postgresql), and [GeoServer](#geoserver). User's [personal workspace](models.md#personal-workspace) is created too.

### Layers
Information about [layers](models.md#layer) includes vector or raster data and visualization.

When user [publishes new layer](rest.md#post-workspace-layers)
- UUID and name is saved to [Redis](#redis) and [filesystem](#filesystem),
- UUID, name, title, description and access rights are to [PostgreSQL](#postgresql),
- data files and visualization file is saved to [filesystem](#filesystem) (if uploaded [synchronously](async-file-upload.md)),
- and asynchronous [tasks](#tasks) are saved in [Redis](#redis).

Subsequently, asynchronous tasks ensure following steps:
- data file chunks and completed data files are saved to [filesystem](#filesystem) (if sent [asynchronously](async-file-upload.md))
- vector data files are imported to [PostgreSQL](#postgresql)
   - files with invalid byte sequence are first converted to GeoJSON, then cleaned with iconv, and finally imported to database.
   - PostgreSQL table with vector data is registered to [GeoServer](#geoserver)
- raster files are normalized and compressed to BigTIFF GeoTIFF with overviews (pyramids)
   - normalized GeoTIFF is registered to [GeoServer](#geoserver)
- SLD file is saved to [GeoServer](#geoserver) and registered to WMS layer
- QGS file is created on [filesystem](#filesystem) and through QGIS server registered to [GeoServer](#geoserver)
- access rights are synchronized to [GeoServer](#geoserver)
- thumbnail file is saved to [filesystem](#filesystem)
- metadata record is saved to [PostgreSQL](#postgresql) using Micka's CSW

When user [patches existing layer](rest.md#patch-workspace-layer), data is saved in the same way.

### Maps
Information about [maps](models.md#map) includes JSON definition.

When user [publishes new map](rest.md#post-workspace-maps)
- UUID and name is saved to [Redis](#redis) and [filesystem](#filesystem),
- UUID, name, title, description and access rights are saved to [PostgreSQL](#postgresql),
- JSON file is saved to [filesystem](#filesystem),
- and asynchronous [tasks](#tasks) are saved in [Redis](#redis).

Subsequently, when asynchronous tasks run,
- relations to [internal layers](models.md#internal-map-layer) are saved to [PostgreSQL](#postgresql)
- thumbnail file is saved to [filesystem](#filesystem)
- and metadata record is saved to [PostgreSQL](#postgresql) using Micka's CSW.

When user [patches existing map](rest.md#patch-workspace-map), data is saved in the same way.

### Tasks
Information about asynchronous tasks consists of few parameters necessary for Celery task runner. In case of publishing or patching layer or map, it includes e.g. task name, owner name, layer/map name, and additional parameters derived from HTTP POST/PATCH parameters.

Task information are saved to [Redis](#redis) only.

### Data version
Information about data version including migration ID is stored in [PostgreSQL](#postgresql).

## Stores
### Redis
Data is saved in LAYMAN_REDIS_URL database. Keys are prefixed with
- Layman python module name that saved the data, followed by `:`, e.g. `layman.layer.geoserver:` or `layman:`
- other strings, e.g. `celery`, `_kombu`, or `unacked` in case of Celery task data.

Redis is used as temporary data store. When Layman stops, data persists in Redis, however on each startup Layman flushes the Redis database and imports user-related data and publication-related data from [filesystem](#filesystem). It means that any [task-related](#tasks) data is lost on startup. This can be controlled by [LAYMAN_SKIP_REDIS_LOADING](env-settings.md#LAYMAN_SKIP_REDIS_LOADING).

### Filesystem
Data is saved to LAYMAN_DATA_DIR directory, LAYMAN_QGIS_DATA_DIR directory, and GeoServer data directory.

**Workspace directory** is created in LAYMAN_DATA_DIR directory for every created [workspace](models.md#workspace). Name of the workspace directory is the same as workspace name.

**Publication directory** is created inside workspace directory for each publication (e.g. map or layer) the user published. Name of the publication directory is the same as name of the publication (e.g. layername or mapname). Publication-related information is saved in publication directory.

**QGIS workspace directory** is created in LAYMAN_QGIS_DATA_DIR directory for every created [workspace](models.md#workspace). Name of the workspace directory is the same as workspace name.

**QGIS layer directory** is created inside QGIS workspace directory for each layer with QGIS style the user published. Name of the publication directory is the same as name of the layer. QGS project with style definition is stored in this directory for WMS purpose.

**Normalized raster directory** named `normalized_raster_data` is created in GeoServer data directory.

**Normalized raster workspace directory** is created in Normalized raster directory for every [workspace](models.md#workspace) with at least one raster layer. Name of the workspace directory is the same as workspace name.

**Normalized raster layer directory** is created inside Normalized raster workspace directory for every raster layer. Name of the publication directory is the same as name of the layer. Normalized raster is stored in this directory for WMS purpose. In case of [timeseries](models.md#timeseries) layer, additional files holding e.g. [time_regex](rest.md#post-workspace-layers) are created too.

Filesystem is used as persistent data store, so data survives Layman restart.
 
### PostgreSQL
Layman uses directly **one database** specified by [LAYMAN_PG_DBNAME](env-settings.md#LAYMAN_PG_DBNAME) to store data. There are three kinds of schemas in such database:
- [LAYMAN_PRIME_SCHEMA](env-settings.md#LAYMAN_PRIME_SCHEMA) that holds information about
   - users, workspaces, and publications including access rights
   - data version including migration ID
- [Internal Role Service Schema](security.md#internal-role-service-schema) with table and view structure that can be used as [role service](security.md#role-service)
- Schemas holding vector layer data.
    - One **[workspace schema](https://www.postgresql.org/docs/13/ddl-schemas.html)** is created for every created [workspace](models.md#workspace). Name of workspace schema is always the same as workspace name.
    - One **[table](https://www.postgresql.org/docs/13/sql-createtable.html)** is created in workspace schema for each layer published with input vector files. Name of the table is in form `layer_<UUID>` with `-` replaced with `_`, e.g. `layer_96b918c6_d88c_42d8_b999_f3992b826958`. The table contains data from vector data files.

**Second database** is used by Micka to store metadata records. The database including its structure is completely managed by Micka. By default, it's named `hsrs_micka6`.

**Other external databases** can be used to publish vector data from PostGIS tables (see `external_table_uri` in [POST Workspace Layers](rest.md#post-workspace-layers)). Layman is able to change data in the table using WFS-T (including adding new columns) if provided DB user has sufficient privileges. Other management is left completely on admin of such DB.

Data changes made directly in vector data DB tables (both internal and external) are automatically propagated to WMS and WFS. However, layer thumbnail and bounding box at Layman are not automatically updated after such changes.

PostgreSQL is used as persistent data store, so data survives Layman restart.

### GeoServer
**[User](https://docs.geoserver.org/2.21.x/en/user/security/webadmin/ugr.html)** is created for every [user](models.md#user) who reserved [username](models.md#username). Username on GeoServer is the same as username on Layman.

Two **[workspaces](https://docs.geoserver.org/2.21.x/en/user/data/webadmin/workspaces.html)** are created, each with one **[PostgreSQL datastore](https://docs.geoserver.org/2.21.x/en/user/data/app-schema/data-stores.html#postgis)**, for every [workspace](models.md#workspace) (both personal and public). First workspace is meant for [WFS](endpoints.md#web-feature-service) and has the same name as the workspace on Layman. Second workspace is meant for [WMS](endpoints.md#web-map-service) and is suffixed with `_wms`. Name of the datastore is `postgresql` for both workspaces. Every workspace-related information (including PostgreSQL datastore) is saved inside workspace.

For each vector layer from external PostGIS table, **[PostgreSQL datastore](https://docs.geoserver.org/2.21.x/en/user/data/app-schema/data-stores.html#postgis)** is created. Name of the data store is `external_db_<layername>`.

For each vector layer with SLD style, **[Feature Type](https://docs.geoserver.org/2.21.x/en/user/rest/api/featuretypes.html)** and **[Layer](https://docs.geoserver.org/2.21.x/en/user/data/webadmin/layers.html)** are registered in both workspaces (WMS and WFS), and **[Style](https://docs.geoserver.org/2.21.x/en/user/styling/webadmin/index.html)** is created in WMS workspace. Names of these three models are the same as layername. Feature type points to appropriate PostgreSQL table through PostgreSQL datastore. Style contains visualization file.

For each vector layer with QML style, **[Feature Type](https://docs.geoserver.org/2.21.x/en/user/rest/api/featuretypes.html)** is registered in WFS workspace, **[Cascading WMS Store](https://docs.geoserver.org/2.21.x/en/user/data/cascaded/wms.html)** and **[Cascading WMS Layer](https://docs.geoserver.org/2.21.x/en/api/#1.0.0/wmslayers.yaml)** are created in WMS workspace. Names of Feature Type and Cascading WMS Layer are the same as layername, name of Cascading WMS Store is prefixed with `qgis_`. Feature type points to appropriate PostgreSQL table through PostgreSQL datastore. Cascading WMS Store and Layer cascades to the layer's WMS instance at QGIS server (pointing to QGS file of the layer).

For each raster layer, **[Coverage Store](https://docs.geoserver.org/2.21.x/en/user/rest/api/coveragestores.html)**, **[Coverage](https://docs.geoserver.org/2.21.x/en/user/rest/api/coverages.html)**, and **[Style](https://docs.geoserver.org/2.21.x/en/user/styling/webadmin/index.html)** are created in WMS workspace. If layer is [timeseries](models.md#timeseries), Coverage Store is [ImageMosaic](https://docs.geoserver.org/2.21.x/en/user/data/raster/imagemosaic/index.html), otherwise it is [GeoTIFF](https://docs.geoserver.org/2.21.x/en/user/data/raster/geotiff.html). Names of Coverage and Style are the same as layername, name of Coverage Store is prefixed with `geotiff_` or `image_mosaic_` depending on its type. Coverage Store and Coverage points to appropriate normalized raster GeoTIFF file(s). Style contains visualization file.

Two **[access rules](https://docs.geoserver.org/2.21.x/en/user/security/layer.html)** are created for each layer in each GeoServer workspace (WFS and WMS), one for [read access right](security.md#publication-access-rights), one for [write access right](security.md#publication-access-rights). Every username from Layman's access right is represented by user's role name (i.e. `USER_<upper-cased username>`). Role `EVERYONE` is represented as `ROLE_ANONYMOUS` and `ROLE_AUTHENTICATED` on GeoServer.

GeoServer is used as persistent data store, so data survives Layman restart.
