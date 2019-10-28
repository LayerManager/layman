# Environment Settings

## LAYMAN_GS_HOST
URL host of GeoServer instance.

## LAYMAN_GS_PORT
URL port of GeoServer instance.

## LAYMAN_GS_USER
Name of [GeoServer user](https://docs.geoserver.org/stable/en/user/security/webadmin/ugr.html#add-user) that Layman uses for authentication and communication with GeoServer. The LAYMAN_GS_USER must be another user than default `admin` user. The LAYMAN_GS_USER user must have at least the [LAYMAN_GS_ROLE](#LAYMAN_GS_ROLE) and default [`ADMIN`](https://docs.geoserver.org/stable/en/user/security/usergrouprole/roleservices.html#mapping-roles-to-system-roles) role (defined by `adminRoleName`).

## LAYMAN_GS_ROLE
Name of [GeoServer role](https://docs.geoserver.org/stable/en/user/security/webadmin/ugr.html#edit-role-service) of [LAYMAN_GS_USER](#LAYMAN_GS_USER). The role is used to create explicit [access rule](https://docs.geoserver.org/stable/en/user/security/layer.html) for all layers published by Layman. The LAYMAN_GS_ROLE must be another role than default [`ADMIN`](https://docs.geoserver.org/stable/en/user/security/usergrouprole/roleservices.html#mapping-roles-to-system-roles) role (defined by `adminRoleName`)! See default development configuration of [roles](deps/geoserver/sample/geoserver_data/security/role/default/roles.xml) and [layer access rights](deps/geoserver/sample/geoserver_data/security/layers.properties).
 
## LAYMAN_PG_DBNAME
Name of [PostgreSQL database](https://www.postgresql.org/docs/9.5/sql-createdatabase.html) in which Layman publishes layer vector data.

## LAYMAN_PG_USER
Name of [PostgreSQL user](https://www.postgresql.org/docs/9.5/sql-createuser.html) that Layman uses for authentication and communication with PostgreSQL. The user needs enough privileges to create new schemas in [LAYMAN_PG_DBNAME](#LAYMAN_PG_DBNAME) database. The LAYMAN_PG_USER must be another user than default `postgres` user! The user also needs access to `public` schema where PostGIS must be installed.

## LAYMAN_REDIS_URL
URL of [Redis logical database](https://redis.io/commands/select) including database number where Layman stores internal data about publications, users, etc.

## LAYMAN_SETTINGS_MODULE
Dotted path to a Python module with Layman settings for Python level.

## LTC_REDIS_URL
URL of [Redis logical database](https://redis.io/commands/select) including database number where Layman Test Client stores user sessions including authentication credentials.

## UID_GID
String with unix-like user identifier and group identifier `<UID>:<GID>`, e.g. `1000:1000`. Suitable for [mounting some volumes as non-root user](./../README.md#mount-some-volumes-as-non-root-user).

