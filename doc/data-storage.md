# Data Storage

Layman stores several types of data in several stores.

Types of data:
- [Users](#users)
- [Layers](#layers)
- [Maps](#maps)
- [Tasks](#tasks) (asynchronous tasks)

Data stores:
- [Redis](#redis)
- [Filesystem](#filesystem)
- [PostgreSQL](#postgresql)
- [GeoServer](#geoserver)

## Types of Data

### Users
Information about users includes their names, contacts, and authentication credentials.

When user [reserves his username](rest.md#patch-current-user), names, contacts and other relevant metadata are [obtained from authorization provider](oauth2/index.md#fetch-user-related-metadata) and saved to [filesystem](#filesystem) and [Redis](#redis).

### Layers
Information about [layers](models.md#layer) includes vector data and visualization.

When user [publishes new layer](rest.md#post-layers)
- UUID and name is saved to [Redis](#redis) and [filesystem](#filesystem),
- UUID, name and title is saved to [PostgreSQL](#postgresql),
- vector data files and visualization file is saved to [filesystem](#filesystem) (if uploaded [synchronously](async-file-upload.md)),
- and asynchronous [tasks](#tasks) are saved in [Redis](#redis).

Subsequently, when asynchronous tasks run,
- vector data file chunks and completed vector data files are saved to [filesystem](#filesystem) (if sent [asynchronously](async-file-upload.md)),
- vector data files are imported to [PostgreSQL](#postgresql),
- PostgreSQL table with vector data is registered to and visualization file is saved to [GeoServer](#geoserver),
- thumbnail file is saved to [filesystem](#filesystem),
- and metadata record is saved to [PostgreSQL](#postgresql) using Micka's CSW.

When user [patches existing layer](rest.md#patch-layer), data is saved in the same way.

### Maps
Information about [maps](models.md#map) includes JSON definition.

When user [publishes new map](rest.md#post-maps)
- UUID and name is saved to [Redis](#redis) and [filesystem](#filesystem),
- UUID, name and title is saved to [PostgreSQL](#postgresql),
- JSON file is saved to [filesystem](#filesystem),
- and asynchronous [tasks](#tasks) are saved in [Redis](#redis).

Subsequently, when asynchronous tasks run,
- thumbnail file is saved to [filesystem](#filesystem)
- and metadata record is saved to [PostgreSQL](#postgresql) using Micka's CSW.

When user [patches existing map](rest.md#patch-map), data is saved in the same way.

### Tasks
Information about asynchronous tasks consists of few parameters necessary for Celery task runner. In case of publishing or patching layer or map, it includes e.g. task name, owner name, layer/map name, and additional parameters derived from HTTP POST/PATCH parameters.

Task information are saved to [Redis](#redis) only.

## Stores
### Redis
Data is saved in LAYMAN_REDIS_URL database. Keys are prefixed with
- Layman python module name that saved the data, followed by `:`, e.g. `layman.layer.geoserver:` or `layman:`
- other strings, e.g. `celery`, `_kombu`, or `unacked` in case of Celery task data.

Redis is used as temporary data store. When Layman stops, data persists in Redis, however on each startup Layman flushes the Redis database and imports user-related data and publication-related data from [filesystem](#filesystem). It means that any [task-related](#tasks) data is lost on startup. This can be controlled by [LAYMAN_SKIP_REDIS_LOADING](env-settings.md#LAYMAN_SKIP_REDIS_LOADING).

### Filesystem
Data is saved to LAYMAN_DATA_DIR directory.

**User directory** is created in LAYMAN_DATA_DIR directory for every user who reserved username. Name of the user directory is the same as username. Every user-related information is saved in user directory.

**Publication directory** is created inside user directory for each publication (e.g. map or layer) the user published. Name of the publication directory is the same as name of the publication (e.g. layername or mapname). Every publication-related information is saved in publication directory.

Filesystem is used as persistent data store, so data survives Layman restart.
 
### PostgreSQL
Layman uses directly **one database** specified by [LAYMAN_PG_DBNAME](env-settings.md#LAYMAN_PG_DBNAME) to store
- general information about users, workspaces, and publications in schema specified by [LAYMAN_PRIME_SCHEMA](env-settings.md#LAYMAN_PRIME_SCHEMA),
- vector layer data.

Vector layer data is organized in schemas and tables:
- **[User schema](https://www.postgresql.org/docs/9.1/ddl-schemas.html)** is created for every user who reserved username. Name of user schema is always the same as username.
- **[Table](https://www.postgresql.org/docs/9.1/sql-createtable.html)** is created in user schema for each layer the user published. Name of the table is the same as layername. The table contains data from vector data files.

**Second database** is used by Micka to store metadata records. The database including its structure is completely managed by Micka. By default, it's named `hsrs_micka6`.

PostgreSQL is used as persistent data store, so data survives Layman restart.

### GeoServer
**[User workspace](https://docs.geoserver.org/stable/en/user/data/webadmin/workspaces.html)** is created and **[PostgreSQL datastore](https://docs.geoserver.org/latest/en/user/data/app-schema/data-stores.html#postgis)** is registered for every user who reserved username. Name of user workspace is always the same as username, name of the datastore is `postgresql`. Every user-related information (including PostgreSQL datastore) is saved in user workspace. Besides workspace and datastore, explicit **[access rule](https://docs.geoserver.org/stable/en/user/security/layer.html)** for all layers in user workspace is created. The rule looks like `<workspace>.*.r=<LAYMAN_GS_ROLE>,ROLE_ANONYMOUS`.
 
**[Feature type](https://docs.geoserver.org/stable/en/user/rest/api/featuretypes.html)** and **[layer](https://docs.geoserver.org/stable/en/user/data/webadmin/layers.html)** is registered in user PostgreSQL datastore and **[style](https://docs.geoserver.org/latest/en/user/styling/webadmin/index.html)** is created in user workspace for each layer the user published. Name of these three models are the same as layername. Every layer-related information is saved in one or more of these three models. Feature type points to appropriate PostgreSQL table. Style contains visualization file.

GeoServer is used as persistent data store, so data survives Layman restart.
