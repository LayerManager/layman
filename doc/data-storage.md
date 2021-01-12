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

When user [reserves his username](rest.md#patch-current-user), names, contacts and other relevant metadata are [obtained from authorization provider](oauth2/index.md#fetch-user-related-metadata) and saved to [filesystem](#filesystem), [Redis](#redis), [PostgreSQL](#postgresql), and [GeoServer](#geoserver). User's [personal workspace](models.md#personal-workspace) is created too.

### Layers
Information about [layers](models.md#layer) includes vector data and visualization.

When user [publishes new layer](rest.md#post-layers)
- UUID and name is saved to [Redis](#redis) and [filesystem](#filesystem),
- UUID, name, title and access rights are to [PostgreSQL](#postgresql),
- vector data files and visualization file is saved to [filesystem](#filesystem) (if uploaded [synchronously](async-file-upload.md)),
- and asynchronous [tasks](#tasks) are saved in [Redis](#redis).

Subsequently, when asynchronous tasks run,
- vector data file chunks and completed vector data files are saved to [filesystem](#filesystem) (if sent [asynchronously](async-file-upload.md)),
- vector data files are imported to [PostgreSQL](#postgresql),
- PostgreSQL table with vector data is registered to, access rights are synchronized to, and visualization file is saved to [GeoServer](#geoserver),
- thumbnail file is saved to [filesystem](#filesystem),
- and metadata record is saved to [PostgreSQL](#postgresql) using Micka's CSW.

When user [patches existing layer](rest.md#patch-layer), data is saved in the same way.

### Maps
Information about [maps](models.md#map) includes JSON definition.

When user [publishes new map](rest.md#post-maps)
- UUID and name is saved to [Redis](#redis) and [filesystem](#filesystem),
- UUID, name, title and access rights are saved to [PostgreSQL](#postgresql),
- JSON file is saved to [filesystem](#filesystem),
- and asynchronous [tasks](#tasks) are saved in [Redis](#redis).

Subsequently, when asynchronous tasks run,
- thumbnail file is saved to [filesystem](#filesystem)
- and metadata record is saved to [PostgreSQL](#postgresql) using Micka's CSW.

When user [patches existing map](rest.md#patch-map), data is saved in the same way.

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
Data is saved to LAYMAN_DATA_DIR directory.

**Workspace directory** is created in LAYMAN_DATA_DIR directory for every created [workspace](models.md#workspace). Name of the workspace directory is the same as workspace name. User-related information is saved in the root of [personal workspace](models.md#personal-workspace) directory.

**Publication directory** is created inside workspace directory for each publication (e.g. map or layer) the user published. Name of the publication directory is the same as name of the publication (e.g. layername or mapname). Publication-related information is saved in publication directory.

Filesystem is used as persistent data store, so data survives Layman restart.
 
### PostgreSQL
Layman uses directly **one database** specified by [LAYMAN_PG_DBNAME](env-settings.md#LAYMAN_PG_DBNAME) to store data. There are two kinds of schemas in such database:
- [LAYMAN_PRIME_SCHEMA](env-settings.md#LAYMAN_PRIME_SCHEMA) that holds information about
   - users, workspaces, and publications including access rights
   - data version including migration ID
- Schemas holding vector layer data.
    - One **[workspace schema](https://www.postgresql.org/docs/9.1/ddl-schemas.html)** is created for every created [workspace](models.md#workspace). Name of workspace schema is always the same as workspace name.
    - One **[table](https://www.postgresql.org/docs/9.1/sql-createtable.html)** is created in workspace schema for each published layer. Name of the table is the same as layername. The table contains data from vector data files.

**Second database** is used by Micka to store metadata records. The database including its structure is completely managed by Micka. By default, it's named `hsrs_micka6`.

PostgreSQL is used as persistent data store, so data survives Layman restart.

### GeoServer
**[User](https://docs.geoserver.org/stable/en/user/security/webadmin/ugr.html)** and **[role](https://docs.geoserver.org/stable/en/user/security/webadmin/ugr.html)** are created for every [user](models.md#user) who reserved [username](models.md#username). User name on GeoServer is the same as username on Layman. Role name is composed a `USER_<upper-cased username>`.

**[Workspace](https://docs.geoserver.org/stable/en/user/data/webadmin/workspaces.html)** is created and **[PostgreSQL datastore](https://docs.geoserver.org/latest/en/user/data/app-schema/data-stores.html#postgis)** is registered for every [workspace](models.md#workspace) (both personal and public). Name of the workspace is always the same on GeoServer as on Layman. Name of the datastore is `postgresql`. Every workspace-related information (including PostgreSQL datastore) is saved inside workspace.

**[Feature type](https://docs.geoserver.org/stable/en/user/rest/api/featuretypes.html)** and **[layer](https://docs.geoserver.org/stable/en/user/data/webadmin/layers.html)** are registered in workspace PostgreSQL datastore and **[style](https://docs.geoserver.org/latest/en/user/styling/webadmin/index.html)** is created in workspace for each layer published on Layman. Name of these three models are the same as layername. Feature type points to appropriate PostgreSQL table. Style contains visualization file.

Two **[access rules](https://docs.geoserver.org/stable/en/user/security/layer.html)** are created for each layer published on Layman, one for [read access right](security.md#publication-access-rights), one for [write access right](security.md#publication-access-rights). Every username from Layman's access right is represented by user's role name (i.e. `USER_<upper-cased username>`). Role `EVERYONE` is represented as `ROLE_ANONYMOUS` on GeoServer.

GeoServer is used as persistent data store, so data survives Layman restart.
