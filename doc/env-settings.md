# Environment Settings

## General Layman settings

### LAYMAN_SETTINGS_MODULE
Dotted path to a Python module with Layman settings for Python level.

### LAYMAN_DATA_DIR
Filesystem directory where most of published data is stored, including data about authentication credentials, users, and publications.

### LAYMAN_SERVER_NAME
String with internal domain and port `<domain>:<port>` of Layman's main instance (not celery worker). Used by thumbnail image generator (Timgen) to call Layman internally. See also [LAYMAN_PROXY_SERVER_NAME](#LAYMAN_PROXY_SERVER_NAME).

### LAYMAN_PROXY_SERVER_NAME
String with public domain and optionally port, e.g. `<domain>` or `<domain>:<port>`.  See also [LAYMAN_SERVER_NAME](#LAYMAN_SERVER_NAME).

### LAYMAN_SKIP_REDIS_LOADING
Set to `true` if you do not want to flush & load redis database on Layman's startup.

### LAYMAN_CELERY_QUEUE
Name of Celery [queue](https://docs.celeryproject.org/en/latest/userguide/routing.html) where Layman's Celery tasks will be sent.

### LAYMAN_CLIENT_VERSION
Git commit hash or tag of [Layman Test Client](https://github.com/jirik/layman-test-client). Referenced version will be used as default client for this Layman instance.

### LAYMAN_CLIENT_URL
Internal URL of [Layman Test Client](https://github.com/jirik/layman-test-client).

### LAYMAN_CLIENT_PUBLIC_URL
Public URL of [Layman Test Client](https://github.com/jirik/layman-test-client).

### LAYMAN_TIMGEN_URL
Internal URL of thumnbail image generator (Timgen) used for generating map thumbnails.

### LAYMAN_OUTPUT_SRS_LIST
List of [EPSG codes](https://en.wikipedia.org/wiki/EPSG_Geodetic_Parameter_Dataset) that will be supported as output spatial reference systems in both WMS and WFS. Value consists of integer codes separated by comma (`,`). If the list does not contain codes [4326](https://epsg.io/4326) and [3857](https://epsg.io/3857), they are appended by Layman automatically.
   - Sample SRS list for World: `4326,3857`
   - Sample SRS list for Czech Republic: `4326,3857,5514,102067,32633,32634`
   - Sample SRS list for Latvia: `4326,3857,3059`

## Layman authentication and authorization

### LAYMAN_AUTHN_MODULES
List of dotted paths to Python modules to be used for authentication. Paths are separated with comma (`,`). Authentication module `layman.authn.http_header` is required by Layman for internal purposes, so even if LAYMAN_AUTHN_MODULES does not contain `layman.authn.http_header` value, the value is appended automatically. See [authentication](security.md#authentication).

### LAYMAN_AUTHN_HTTP_HEADER_NAME
Secret name of HTTP header used for authentication internally (e.g. when generating private map thumbnail). Only combination of lowercase characters and numbers must be used for the value. At demo configuration, the HTTP header is automatically removed by Nginx on every request to Layman REST API or to GeoServer WMS/WFS/OWS.

### LAYMAN_AUTHN_OAUTH2_PROVIDERS
List of dotted paths to Python modules to be used as OAuth2 providers. Paths are separated with comma (`,`). See [OAuth2](oauth2/index.md).

### OAUTH2_LIFERAY_CLIENT_ID
Client ID of Layman's Test Client registered as OAuth2 provider at Liferay instance.

### OAUTH2_LIFERAY_CLIENT&lt;n&gt;_ID
Client ID of another Layman's client registered as OAuth2 provider at Liferay instance. The **n** must be integer starting from `1`. In case of more clients other than LTC, list of **n**s must be uninterrupted series of integers.

### OAUTH2_LIFERAY_SECRET
Client secret of Layman's Test Client registered as OAuth2 provider at Liferay instance.

### OAUTH2_LIFERAY_SECRET&lt;n&gt;
Client secret of another Layman's Test client registered as OAuth2 provider at Liferay instance. The **&lt;n&gt;** corresponds with [OAUTH2_LIFERAY_CLIENT&lt;n&gt;_ID](#OAUTH2_LIFERAY_CLIENTn_ID). Do not set client secret for OAuth2 Authorization Code flow with PKCE.

### OAUTH2_LIFERAY_AUTH_URL
URL of Liferay OAuth2 Authorization endpoint.

### OAUTH2_LIFERAY_TOKEN_URL
URL of Liferay OAuth2 Token endpoint. Used by LTC only.

### OAUTH2_LIFERAY_CALLBACK_URL
URL of LTC OAuth2 callback endpoint to be called after Liferay authorization. Used by LTC only.

### OAUTH2_LIFERAY_INTROSPECTION_URL
URL of Liferay OAuth2 Introspection endpoint.

### OAUTH2_LIFERAY_USER_PROFILE_URL
URL of Liferay User Profile endpoint.

### GRANT_CREATE_PUBLIC_WORKSPACE
List of [users](models.md#user) and [roles](models.md#role) giving them permission to create new [public workspace](models.md#public-workspace). It must be subset of (or equal to) GRANT_PUBLISH_IN_PUBLIC_WORKSPACE.

### GRANT_PUBLISH_IN_PUBLIC_WORKSPACE
List of [users](models.md#user) and [roles](models.md#role) giving them permission to publish new [publication](models.md#publication) in already created [public workspace](models.md#public-workspace).

## Layman Test Client Settings

### LTC_BASEPATH
URL path of [Layman Test Client](https://github.com/jirik/layman-test-client).

### LTC_LAYMAN_USER_PROFILE_URL
Internal URL of REST API [Current User](rest.md#current-user) endpoint.

### LTC_LAYMAN_REST_URL
Internal URL (only protocol & host & port, without path) of Layman's REST API.

### LTC_REDIS_URL
URL of [Redis logical database](https://redis.io/commands/select) including database number where Layman Test Client stores user sessions including authentication credentials.

### LTC_SESSION_SECRET
See [`secret` at express-session documentation](https://www.npmjs.com/package/express-session#secret).

### LTC_SESSION_MAX_AGE
See [`cookie.maxAge` at express-session documentation](https://www.npmjs.com/package/express-session#cookiemaxage).

## Connection to Redis

### LAYMAN_REDIS_URL
URL of [Redis logical database](https://redis.io/commands/select) including database number. Layman stores internal data about publications and users in this database. By default, Layman flushes the whole logical database on every startup! See also [LAYMAN_SKIP_REDIS_LOADING](#LAYMAN_SKIP_REDIS_LOADING).

## Connection to PostgreSQL

### LAYMAN_PG_HOST
Internal URL host of PostgreSQL instance.

### LAYMAN_PG_PORT
Internal URL port of PostgreSQL instance.

### LAYMAN_PG_DBNAME
Name of [PostgreSQL database](https://www.postgresql.org/docs/9.5/sql-createdatabase.html) in which Layman publishes layer vector data.

### LAYMAN_PG_USER
Name of [PostgreSQL user](https://www.postgresql.org/docs/9.5/sql-createuser.html) that Layman uses for authentication and communication with PostgreSQL. The user needs enough privileges to create new schemas in [LAYMAN_PG_DBNAME](#LAYMAN_PG_DBNAME) database. The LAYMAN_PG_USER must be another user than default `postgres` user! The user also needs access to `public` schema where PostGIS must be installed.

### LAYMAN_PG_PASSWORD
Password of [LAYMAN_PG_USER](#LAYMAN_PG_USER).

### LAYMAN_PRIME_SCHEMA
Name of Layman data schema in PostgreSQL database. Information about users, publications, access rights, and [more](data-storage.md#postgresql) is stored in this schema. This name have to starts with lowercase character or underscore, followed by lowercase characters, numbers or underscores. Also, it must be different from existing [workspace name](models.md#workspace). Value should not be changed after first start of Layman. 

## Connection to GeoServer

### GEOSERVER_ADMIN_PASSWORD
Password of GeoServer `admin` user. If provided, it will be used to automatically create Layman user [LAYMAN_GS_USER](#LAYMAN_GS_USER) and Layman role [LAYMAN_GS_ROLE](#LAYMAN_GS_ROLE) on Layman's startup.

### LAYMAN_GS_HOST
Internal URL host of GeoServer instance.

### LAYMAN_GS_PORT
Internal URL port of GeoServer instance.

### LAYMAN_GS_PATH
URL path of GeoServer instance.

### LAYMAN_GS_USER
Name of [GeoServer user](https://docs.geoserver.org/stable/en/user/security/webadmin/ugr.html#add-user) that Layman uses for authentication and communication with GeoServer. The LAYMAN_GS_USER must be another user than default `admin` user. The LAYMAN_GS_USER user must have at least the [LAYMAN_GS_ROLE](#LAYMAN_GS_ROLE) and default [`ADMIN`](https://docs.geoserver.org/stable/en/user/security/usergrouprole/roleservices.html#mapping-roles-to-system-roles) role (defined by `adminRoleName`). The user and his required roles will be created automatically on Layman's startup if [GEOSERVER_ADMIN_PASSWORD](#GEOSERVER_ADMIN_PASSWORD) is provided.

### LAYMAN_GS_PASSWORD
Password of [LAYMAN_GS_USER](#LAYMAN_GS_USER).

### LAYMAN_GS_ROLE
Name of [GeoServer role](https://docs.geoserver.org/stable/en/user/security/webadmin/ugr.html#edit-role-service) of [LAYMAN_GS_USER](#LAYMAN_GS_USER). The role is used to create explicit [access rule](https://docs.geoserver.org/stable/en/user/security/layer.html) for all layers published by Layman. The LAYMAN_GS_ROLE must be another role than default [`ADMIN`](https://docs.geoserver.org/stable/en/user/security/usergrouprole/roleservices.html#mapping-roles-to-system-roles) role (defined by `adminRoleName`)! The role will be created automatically if [GEOSERVER_ADMIN_PASSWORD](#GEOSERVER_ADMIN_PASSWORD) is provided.
 
### LAYMAN_GS_PROXY_BASE_URL
GeoServer [Proxy Base URL](https://docs.geoserver.org/stable/en/user/configuration/globalsettings.html). It is automatically set on Layman's startup. If you do not set the variable, value is calculated as [LAYMAN_CLIENT_PUBLIC_URL](#LAYMAN_CLIENT_PUBLIC_URL)+[LAYMAN_GS_PATH](#LAYMAN_GS_PATH). If you set it to empty string, no change of Proxy Base URL will be done on GeoServer side.

### LAYMAN_GS_USER_GROUP_SERVICE
Name of [user/group service](https://docs.geoserver.org/stable/en/user/security/usergrouprole/usergroupservices.html) used for managing users at GeoServer. If not set (default), the service named `default` is chosen. Usually it's [XML user/group service](https://docs.geoserver.org/stable/en/user/security/usergrouprole/usergroupservices.html#xml-user-group-service).

### LAYMAN_GS_ROLE_SERVICE
Name of [role service](https://docs.geoserver.org/stable/en/user/security/usergrouprole/roleservices.html) used for managing roles and user-role associations at GeoServer. If not set (default), the service named `default` is chosen. Usually it's [XML user/group service](https://docs.geoserver.org/stable/en/user/security/usergrouprole/roleservices.html#xml-role-service).

### LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE
Secret value of [GeoServer HTTP authentication request header attribute](https://docs.geoserver.org/stable/en/user/security/tutorials/httpheaderproxy/index.html) used for WFS proxy. Only combination of lowercase characters and numbers must be used for the value. If you change an existing value, you have to change it also in GeoServer GUI manually.

## Connection to Micka

### CSW_BASIC_AUTHN
HTTP Basic Authentication credentials for communication with [CSW](#CSW_URL) encoded as `user:password`.

### CSW_RECORD_URL
URL of [CSW](#CSW_URL) metadata record accessible by web browser, probably with some editing capabilities. Must contain `{identifier}` string that will be replaced with record ID.

### CSW_URL
Internal URL of [OGC Catalogue Service v2.0.2](https://www.opengeospatial.org/standards/cat) endpoint. Tested with [Micka](http://micka.bnhelp.cz/).

### CSW_PROXY_URL
Public URL of [OGC Catalogue Service v2.0.2](https://www.opengeospatial.org/standards/cat) endpoint. Tested with [Micka](http://micka.bnhelp.cz/).

### MICKA_ACCEPTED_VERSION
Version of Micka that Layman will accept on startup encoded as `version:revision`, e.g. `2020.014:2020-04-15.01`. If it is not set, a version defined in [LAYMAN_SETTINGS_MODULE](#LAYMAN_SETTINGS_MODULE) will be accepted.

### MICKA_HOSTPORT
String with public domain and optionally port, e.g. `<domain>` or `<domain>:<port>`. Passed as configuration to Micka for demo purposes.

## Flask settings

### FLASK_APP
See [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/cli/#application-discovery).

### FLASK_ENV
See [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/config/#environment-and-debug-features).

### FLASK_SECRET_KEY
See [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY).

## Docker settings

### UID_GID
String with unix-like user identifier and group identifier `<UID>:<GID>`, e.g. `1000:1000`. Suitable for [mounting some volumes as non-root user](./../README.md#mount-some-volumes-as-non-root-user).

