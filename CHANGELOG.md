# Changelog

## v1.10.0
  {release-date}
### Upgrade requirements
- If you are running Layman with development settings, set environment variables
  - [LAYMAN_QGIS_HOST](doc/env-settings.md#LAYMAN_QGIS_HOST)=nginx-qgis
  - [LAYMAN_QGIS_PORT](doc/env-settings.md#LAYMAN_QGIS_PORT)=80
  - [LAYMAN_QGIS_PATH](doc/env-settings.md#LAYMAN_QGIS_PATH)=/qgis/
### Migrations and checks
- [#154](https://github.com/jirik/layman/issues/154) All workspaces are checked, that their name did not end with '_wms'. With any of the workspaces ended with the suffix, startup process is stopped with error code 45. In that case, please downgrade to the previous minor release version and contact Layman contributors.
- [#154](https://github.com/jirik/layman/issues/154) All layers are copied into [dedicated WMS GeoServer workspace](doc/data-storage.md#geoserver). Styles are also moved into that workspace.
### Changes
- [#154](https://github.com/jirik/layman/issues/154) [WMS](doc/endpoints.md#web-map-service) is available in dedicated [GeoServer workspace](doc/data-storage.md#geoserver) whose name is composed from Layman's [workspace](doc/models.md#workspace) name and suffix `_wms`. [WFS](doc/endpoints.md#web-feature-service) remains in GeoServer workspace whose name is equal to Layman's workspace name.
- [#154](https://github.com/jirik/layman/issues/154) SLD style published in dedicated WMS GeoServer workspace.
- [#99](https://github.com/jirik/layman/issues/99) New endpoint [`/rest/about/version'](doc/rest.md#get-version). Also available in Layman Test Client.
- [#154](https://github.com/jirik/layman/issues/154) Workspace name can not end with '_wms'. In such case, error with code 45 is raised.
- New environment variables [LAYMAN_QGIS_HOST](doc/env-settings.md#LAYMAN_QGIS_HOST), [LAYMAN_QGIS_PORT](doc/env-settings.md#LAYMAN_QGIS_PORT), and [LAYMAN_QGIS_PATH](doc/env-settings.md#LAYMAN_QGIS_PATH).
- [#154](https://github.com/jirik/layman/issues/154) For endpoints [POST Layers](doc/rest.md#post-layers) and [PATCH Layer](doc/rest.md#patch-layer), parameter *sld* is replaced by the new parameter *style* and marked as deprecated. In response to endpoints [GET Layer](doc/rest.md#get-layer) and [PATCH Layer](doc/rest.md#patch-layer), *sld* is replaced by the new *style* item and marked as deprecated.


## v1.9.1
 2021-01-18
### Upgrade requirements
- If you are migrating from v1.9.0 with `5514` included in [LAYMAN_OUTPUT_SRS_LIST](doc/env-settings.md#LAYMAN_OUTPUT_SRS_LIST), you need to manually replace definition of 5514 in `deps/geoserver/data/user_projections/epsg.properties` file with
    ```
    5514=PROJCS["S-JTSK / Krovak East North",GEOGCS["S-JTSK",DATUM["System Jednotne Trigonometricke Site Katastralni",SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],TOWGS84[572.213,85.334,461.94,4.9732,-1.529,-5.2484,3.5378],AUTHORITY["EPSG","6156"]],PRIMEM["Greenwich",0.0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.017453292519943295],AXIS["Geodetic longitude",EAST],AXIS["Geodetic latitude", NORTH],AUTHORITY["EPSG","4156"]],PROJECTION["Krovak",AUTHORITY["EPSG","9819"]],PARAMETER["latitude_of_center",49.5],PARAMETER["longitude_of_center",24.833333333333332],PARAMETER["azimuth", 30.288139722222223],PARAMETER["pseudo_standard_parallel_1",78.5],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",0.0],PARAMETER["false_northing",0.0],UNIT["m", 1.0],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","5514"]]
    ```
    and restart GeoServer.

### Changes
- [#228](https://github.com/jirik/layman/issues/228) Fixed shift in EPSG:5514.
- [#227](https://github.com/jirik/layman/issues/227) Flower is accessible in demo configuration again.

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
- GeoServer's security rules of each publication are recalculated according to publication's access rights. It fixes [#200](https://github.com/jirik/layman/issues/200) also for existing layers.
- Mistakenly created users and roles in GeoServer, created for public workspaces, are deleted.

### Changes
- One of [OAuth2 HTTP headers](doc/oauth2/index.md#request-layman-rest-api), `AuthorizationIssUrl`, is optional if and only if there is only one OAuth2 authorization server registered at Layman. The header was mandatory in 1.8.0 and sooner.
- Information about data version including migration ID is stored in [PostgreSQL](doc/data-storage.md#data-version).
- When public workspace is created, only workspace is created on GeoServer. Previously also user and roles were mistakenly created.

## v1.8.1
 2021-01-06
### Upgrade notes
- The fix of [#200](https://github.com/jirik/layman/issues/200) affects only newly posted or patched layers. To fix access rights on existing layers, you can either wait for 1.9 release (2021-01-15), or manually add ROLE_AUTHENTICATED for every [layer security rule](https://docs.geoserver.org/stable/en/user/security/layer.html) which already contains ROLE_ANONYMOUS.
### Changes
- [#200](https://github.com/jirik/layman/issues/200) Access rights EVERYONE is correctly propagated to GeoServer also for authenticated users. Only newly posted or patched layers are affected by the fix.
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
- [#28](https://github.com/jirik/layman/issues/28) It is possible to control also [read access](doc/security.md#publication-access-rights) to any publication per user.
   - New attribute `access_rights` added to [GET Layers](doc/rest.md#get-layers), [GET Layer](doc/rest.md#get-layer), [GET Maps](doc/rest.md#get-maps) and [GET Map](doc/rest.md#get-map) responses.
   - New parameters `access_rights.read` and `access_rights.write` added to [POST Layers](doc/rest.md#post-layers), [PATCH Layer](doc/rest.md#patch-layer), [POST Maps](doc/rest.md#post-maps) and [PATCH Map](doc/rest.md#patch-map) requests. These new parameters are added to Test Client GUI.
   - Default values of access rights parameters (both read and write) of newly created publications are set to current authenticated user, or EVERYONE if published by anonymous.
- [#28](https://github.com/jirik/layman/issues/28) At first start of Layman, access rights of existing publications are set in following way:
    - [everyone can read and only owner of the workspace can edit](doc/security.md#Authorization) publications in [personal workspaces](doc/models.md#personal-workspace)
    - [anyone can read or edit](doc/security.md#Authorization) publications in [public workspaces](doc/models.md#public-workspace).
    - Security rules on GeoServer on [workspace level (workspace.*.r/w)](https://docs.geoserver.org/stable/en/user/security/layer.html) are deleted and replaced with security rules on [layer level (workspace.layername.r/w)](https://docs.geoserver.org/stable/en/user/security/layer.html) according to rules on Layman side.
- [#28](https://github.com/jirik/layman/issues/28) Only publications with [read access](doc/security.md#publication-access-rights) for EVERYONE are published to Micka as public.
- [#28](https://github.com/jirik/layman/issues/28) New REST endpoint [GET Users](doc/rest.md#get-users) with list of all users registered in Layman. This new endpoint was added to Test Client into tab "Others".
- [#28](https://github.com/jirik/layman/issues/28) [WMS endpoint](doc/endpoints.md#web-map-service) accepts same [authentication](doc/security.md#authentication) credentials (e.g. [OAuth2 headers](doc/oauth2/index.md#request-layman-rest-api)) as Layman REST API endpoints. It's implemented using Layman's WFS proxy. This proxy authenticates the user and send user identification to GeoServer.
- [#161](https://github.com/jirik/layman/issues/161) New method DELETE was implemented for endpoints [DELETE Maps](doc/rest.md#delete-maps) and [DELETE Layers](doc/rest.md#delete-layers).
- [#178](https://github.com/jirik/layman/issues/178) New attribute `screen_name` is part of response for [GET Users](doc/rest.md#get-users) and [Get Current User](doc/rest.md#get-current-user).
- [#178](https://github.com/jirik/layman/issues/178) LifeRay attribute `screen_name` is preferred for creating username in Layman. Previously it was first part of email.
- Attribute `groups` is no longer returned in [GET Map File](doc/rest.md#get-map-file) response.
- [#28](https://github.com/jirik/layman/issues/28) New environment variable [LAYMAN_PRIME_SCHEMA](doc/env-settings.md#LAYMAN_PRIME_SCHEMA). 

## v1.7.4
2020-12-14
### Changes
- [#175](https://github.com/jirik/layman/issues/175) Fix posting new layer caused by [v1.7.3](#v173).

## v1.7.3
2020-11-30
### :warning: Attention :warning:
There is a critical bug in this release, posting new layer breaks Layman: https://github.com/jirik/layman/issues/175 It's solved in [v1.7.4](#v174).

### Changes
- If published [layer](doc/models.md#layer) has empty bounding box (i.e. no features), its bounding box on WMS/WFS endpoint is set to the whole World. This happens on [POST Layers](doc/rest.md#post-layers) and [PATCH Layer](doc/rest.md#patch-layer).
- [#40](https://github.com/jirik/layman/issues/40) Enable to upload empty ShapeFile.

## v1.7.2
2020-11-09
### Changes
- [#133](https://github.com/jirik/layman/issues/133) Attribute `url` of [GET Maps](doc/rest.md#get-maps) response was repaired. Previously, it incorrectly used map name instead of username in the URL path.

## v1.7.1
2020-09-30
### Upgrade requirements
- Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) to `v1.3.0`
    - If you are running Layman with development settings, run also `make client-build`.
### Changes
- Test Client contains also GET Layer Style endpoint.
- Return real SLD style in GET Layer Style instead of just metadata
- [#109](https://github.com/jirik/layman/issues/109) Handle records without title in GET Layers / GET Maps

## v1.7.0
2020-09-30
### Upgrade requirements
- [#65](https://github.com/jirik/layman/issues/65) Set environment variable [LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE](doc/env-settings.md#LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE). Only combination of lowercase characters and numbers must be used for the value.
- [#101](https://github.com/jirik/layman/issues/101) Change [LAYMAN_CLIENT_VERSION](doc/env-settings.md#LAYMAN_CLIENT_VERSION) from `v1.1.2` to `v1.2.0`
    - If you are running Layman with development settings, run also `make client-build`.
### Changes
- [#65](https://github.com/jirik/layman/issues/65) [WFS endpoint](doc/endpoints.md#web-feature-service) accepts same [authentication](doc/security.md#authentication) credentials (e.g. [OAuth2 headers](doc/oauth2/index.md#request-layman-rest-api)) as Layman REST API endpoints. It's implemented using Layman's WFS proxy. This proxy authenticates the user and send user identification to GeoServer. In combination with changes in v1.6.0, Layman's [`read-everyone-write-owner` authorization](doc/security.md#authorization) (when active) is propagated to GeoServer and user can change only hers layers.
- [#88](https://github.com/jirik/layman/issues/88) Attribute **title** was added to REST endpoints [GET Layers](doc/rest.md#get-layers) and [GET Maps](doc/rest.md#get-maps).
- [#95](https://github.com/jirik/layman/issues/95) When calling WFS Transaction, Layman will automatically create missing attributes in DB before redirecting request to GeoServer. Each missing attribute is created as `VARCHAR(1024)`. Works for WFS-T 1.0, 1.1 and 2.0, actions Insert, Update and Replace. If creating attribute fails for any reason, warning is logged and request is redirected nevertheless.
- [#96](https://github.com/jirik/layman/issues/96) New REST API endpoint [Layer Style](doc/rest.md#get-layer-style) is created, which returns Layer default SLD. New attribute ```sld.url``` is added to [GET Layer endpoint](doc/rest.md#get-layer), where URL of Layer default SLD can be obtained. It points to above mentioned [Layer Style](doc/rest.md#get-layer-style).
- [#101](https://github.com/jirik/layman/issues/101) Test Client has new page for WFS proxy and is capable to send authenticated queries.
- [#65](https://github.com/jirik/layman/issues/65) Layman automatically setup [HTTP authentication attribute](https://docs.geoserver.org/stable/en/user/security/tutorials/httpheaderproxy/index.html) and chain filter at startup. Secret value of this attribute can be changed in [LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE](doc/env-settings.md#LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE) and is used by Layman's WFS proxy.

## v1.6.1
2020-08-19
- [#97](https://github.com/jirik/layman/issues/97) Before v1.6, [reserved `username`](doc/rest.md#patch-current-user) could be the same as LAYMAN_GS_USER. Starting at 1.6, this leads to conflict of two GeoServer users with the same name. This patch release comes with detection of this conflict (Layman error code 41).
   - If you encounter error 41, you can resolve the conflict by following steps:
       - In GeoServer GUI, create new GeoServer user with another name to become new LAYMAN_GS_USER and give him LAYMAN_GS_ROLE and ADMIN roles
       - In GeoServer GUI, remove the old LAYMAN_GS_USER user
       - Change environment settings LAYMAN_GS_USER and LAYMAN_GS_PASSWORD for the new GeoServer user
       - Restart Layman

## v1.6.0
2020-08-19
### Upgrade requirements
- [#69](https://github.com/jirik/layman/issues/69) If you are running Layman with development or test settings, set [LAYMAN_SETTINGS_MODULE](doc/env-settings.md#LAYMAN_SETTINGS_MODULE) in your `.env` file to `layman_settings`. No action is required if you are running Layman based on demo settings (probably all production instances).
### Changes
- [#74](https://github.com/jirik/layman/issues/74) Layman user and role at GeoServer defined by [LAYMAN_GS_USER](doc/env-settings.md#LAYMAN_GS_USER) and [LAYMAN_GS_ROLE](doc/env-settings.md#LAYMAN_GS_ROLE) are now created automatically on Layman's startup if an only if new environment variable [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) is provided. There is no need to set [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) for other reason than automatically creating Layman user and Layman role.
   - No change is required. If you are migrating existing instance, Layman user and role are already created, so you don't need to set [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD). If this is your first Layman release, [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD) is set in `.env` files starting with this version, so Layman user and role at GeoServer will be automatically created on startup.
   - No need to run command `make geoserver-reset-default-datadir` from now on. This command was removed from make options.
- [#62](https://github.com/jirik/layman/issues/62) GeoServer [Proxy Base URL](https://docs.geoserver.org/stable/en/user/configuration/globalsettings.html) is now automatically set on Layman's startup according to [LAYMAN_GS_PROXY_BASE_URL](doc/env-settings.md#LAYMAN_GS_PROXY_BASE_URL). If you do not set the variable, value is calculated as [LAYMAN_CLIENT_PUBLIC_URL](doc/env-settings.md#LAYMAN_CLIENT_PUBLIC_URL)+[LAYMAN_GS_PATH](doc/env-settings.md#LAYMAN_GS_PATH). If you set it to empty string, no change of Proxy Base URL will be done on GeoServer side.
- [#83](https://github.com/jirik/layman/issues/89) All layers are created as `GEOMETRY` type, so any other type can be added (for example polygons can be added to points).
- [#73](https://github.com/jirik/layman/issues/73) Layman users are automatically created on GeoServer (either at start up of Layman or when reserved) with separate role and workspace. Username is the same as in Layman, name of role is `"USER_"+username`, name of workspace is the same as username. Read and write permissions for workspace are set according to Layman's authorization (as of now read-everyone-write-everyone or read-everyone-write-owner).
- New environment variables [LAYMAN_GS_USER_GROUP_SERVICE](doc/env-settings.md#LAYMAN_GS_USER_GROUP_SERVICE) and [LAYMAN_GS_ROLE_SERVICE](doc/env-settings.md#LAYMAN_GS_ROLE_SERVICE) enable to control which user/group and role services are used at GeoServer. Not setting these variables means to use default services. 
- [#69](https://github.com/jirik/layman/issues/69) Three separate identical settings files (`layman_settings_demo.py`, `layman_settings_dev.py`, `layman_settings_test.py`) were merged into one file `layman_settings.py`.
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
- Remove [CSW_ORGANISATION_NAME_REQUIRED](https://github.com/jirik/layman/blob/v1.2.1/doc/env-settings.md) from environment settings
- If you are using Layman's `make` commands with `-d` suffix, use these commands without the `-d` suffix from now on (e.g. `make start-demo-full-d` becomes `make start-demo-full`).

### Changes
- Both [PATCH Layer](doc/rest.md#patch-layer) and [PATCH Map](doc/rest.md#patch-map) automatically update also CSW metadata records.
- Use absolute URLs in responses of Layer and Map endpoints
- Add [GET Layer Metadata Comparison](doc/rest.md#get-layer-metadata-comparison) and [GET Map Metadata Comparison](doc/rest.md#get-map-metadata-comparison) endpoints. 
- Add [`revision_date`](doc/metadata.md#revision_date) metadata property
- Add `metadata.comparison_url` to [GET Layer](doc/rest.md#get-layer) and [GET Map](doc/rest.md#get-map) responses.
- Upgrade Layman test client to version 1.1.1
- Environment settings [CSW_ORGANISATION_NAME_REQUIRED](https://github.com/jirik/layman/blob/v1.2.1/doc/env-settings.md) is not used anymore as Micka v2020 accepts records without organisation names. 
- Metadata properties [wms_url](doc/metadata.md#wms_url) and [wfs_url](doc/metadata.md#wfs_url) point directly to GetCapabilities documents. 
- Layman now uses WMS 1.3.0 and WFS 2.0.0 in communication with GeoServer and in CSW metadata records.
- All `make` commands with `docker-compose up` now run in the background. Foreground running was removed. Use `docker logs` to inspect container logs. 
 

## v1.2.1
2020-03-20
### Upgrade requirements
- Change [CSW_URL](doc/env-settings.md#CSW_URL) from `http://micka:80/csw` to `http://micka:80/micka/csw`

### Changes
- Fix URL prefix of Micka GUI in Layman v1.2.0, [#49](https://github.com/jirik/layman/issues/49) 

## v1.2.0
2020-03-18

### Upgrade requirements
- Upgrade Micka to [v2020.010](https://github.com/hsrs-cz/Micka/releases/tag/v2020.010).
- Add [CSW_PROXY_URL](doc/env-settings.md#CSW_PROXY_URL) to distinguish between internal CSW URL for Layman and public CSW URL for clients.
- Rename host of [LAYMAN_TIMGEN_URL](doc/env-settings.md#LAYMAN_TIMGEN_URL) from `hslayers` to `timgen`.
- Add [MICKA_HOSTPORT](doc/env-settings.md#MICKA_HOSTPORT) for demo run.

### Changes
- Publish metadata record of [map](doc/models.md#map) to Micka on [POST Maps](doc/rest.md#post-maps).
- Add `metadata` info to [GET Map](doc/rest.md#get-map) response.
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
- Treat attribute names in SLD (aka 'launder'), [#45](https://github.com/jirik/layman/issues/45)
- Fix Micka's About URL in wait_for_deps
- Assert version of Micka on startup.
- Load data into redis on startup even in Flower.
- Better handle Micka's HTTP errors, [#43](https://github.com/jirik/layman/issues/43)
- Rename hslayers container to timgen (Thumbnail Image Generator)

## v1.1.8
2020-03-16
- Treat attribute names in SLD (aka 'launder'), [#45](https://github.com/jirik/layman/issues/45)
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
- Better handle Micka's HTTP errors, [#43](https://github.com/jirik/layman/issues/43)

## v1.1.3
2020-01-31
- Improve documentation of [enviroment variables](doc/env-settings.md)
- Show real info instead of just SUCCESS status in successfully finished tasks within GET Layer, GET Map, etc.
- Check freshness of links and image URLs in documentation within CI
- Add few words about Layman in [EN](doc/about.md) ans [CS](doc/cs/o-aplikaci.md)

## v1.1.2
2019-12-26
- Allow requesting layman from other docker containers (fix [#38](https://github.com/jirik/layman/issues/38))

## v1.1.1
2019-12-23
- Fix PENDING in state after celery task is removed from redis

## v1.1.0
2019-12-23
- Publish metadata record of [layer](doc/models.md#layer) to Micka on [POST Layers](doc/rest.md#post-layers). Connection to Micka is configurable using [CSW_*](doc/env-settings.md) environment variables.
- Delete metadata record of layer from Micka on [DELETE Layer](doc/rest.md#delete-layer).
- Add `metadata` info to [GET Layer](doc/rest.md#get-layer) response, including CSW URL and metadata record URL.
- [Documentation of metadata](doc/metadata.md)
- [LAYMAN_PROXY_SERVER_NAME](doc/env-settings.md#LAYMAN_PROXY_SERVER_NAME) environment variable
- Do not depend on specific version of chromium-browser and chromedriver
- Save write-lock to redis on POST, PATCH and DELETE of Layer and Map
- Enable to run Layman using multiple WSGI Flask processes by moving information about tasks from memory to redis
- Use Flask decorators
- Unify async task names, call task methods in the same way (src/layman/common/tasks.py#get_task_methods, src/layman/common/tasks.py#get_task_methods#tasks_util.get_chain_of_methods, src/layman/celery.py#set_publication_task_info)
