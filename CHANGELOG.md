# Changelog

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
- [#65](https://github.com/jirik/layman/issues/65) [WFS endpoint](doc/rest.md#get-layer) accepts same [authentication](doc/security.md#authentication) credentials (e.g. [OAuth2 headers](doc/oauth2/index.md#request-layman-rest-api)) as Layman REST API endpoints. It's implemented using Layman's WFS proxy. This proxy authenticates the user and send user identification to GeoServer. In combination with changes in v1.6.0, Layman's [`read-everyone-write-owner` authorization](doc/security.md#authorization) (when active) is propagated to GeoServer and user can change only hers layers.
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
