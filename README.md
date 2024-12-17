# layman
![IntegrationTests](https://github.com/LayerManager/layman/workflows/IntegrationTests/badge.svg?branch=master)

Publishing geospatial data online through [REST API](doc/rest.md).

- Two publication models available:
  - [**layer**](doc/models.md#layer): visual representation of single vector or raster dataset, including raster [timeseries](doc/models.md#timeseries)
  - [**map**](doc/models.md#map): collection of layers
- Accepts **vector** layer data in [GeoJSON](https://en.wikipedia.org/wiki/GeoJSON), [ShapeFile](https://en.wikipedia.org/wiki/Shapefile), or [PostGIS table](https://postgis.net/) identified by [PostgreSQL connection URI](https://www.postgresql.org/docs/15/libpq-connect.html#id-1.7.3.8.3.6)
- Accepts **raster** layer data in [GeoTIFF](https://gdal.org/en/stable/drivers/raster/gtiff.html), [JPEG2000](https://gdal.org/en/stable/drivers/raster/jp2openjpeg.html), [PNG](https://gdal.org/en/stable/drivers/raster/png.html), and [JPEG](https://gdal.org/en/stable/drivers/raster/jpeg.html) formats
- Accepts layer **style** in [Styled Layer Descriptor](https://www.ogc.org/publications/standard/sld/), [Symbology Encoding](https://www.ogc.org/publications/standard/se/), and [QGIS Style File Format](https://docs.qgis.org/3.16/en/docs/user_manual/appendices/qgis_file_formats.html#qml-the-qgis-style-file-format) (for vector data only) formats
- Accepts **map** definition in [HSLayers Map Composition](https://github.com/hslayers/map-compositions) format
- Even large files can be easily uploaded from browser thanks to asynchronous chunk upload
- [OAuth2 authentication](doc/security.md#authentication)
- [Authorization](doc/security.md#authorization) enables to set read and write access to each layer and map for specific users
- Asynchronous processing
- Provides URL endpoints
  - [REST API](doc/rest.md)
  - [Web Map Service (WMS)](doc/endpoints.md#web-map-service)
  - [Web Feature Service (WFS)](doc/endpoints.md#web-feature-service)
  - [Catalogue Service (CSW)](doc/endpoints.md#catalogue-service)
- Documented [security system](doc/security.md), [data storage](doc/data-storage.md), and [proxying](doc/client-proxy.md)
- Configurable by environment variables
- Standing on the shoulders of Docker, Python, Flask, PostgreSQL, PostGIS, GDAL, QGIS Server, GeoServer, OpenLayers, Celery, Redis, and [more](doc/dependencies.md)
- Inspired by [CCSS-CZ/layman](https://github.com/CCSS-CZ/layman)


## Requirements
- at least 3 GB RAM
- at least 5 GB disk space
- Linux kernel v4.11+ (because of QGIS server and its Qt 5.10+/libQt5Core dependency), for example
  - Ubuntu 18.04.2+
  - CentOS 8+
  - Fedora 29+

    You can check your kernel version with `uname -r`.
- Docker Engine v20.10.13+ including Docker Compose v2+
  - installation instructions for [centos 7](https://docs.docker.com/engine/install/centos/), including docker-compose-plugin installation

**Optionally**
- linux or any tool to run tasks defined in Makefile using `make` command
   - can be replaced by running commands defined in [Makefile](Makefile) directly
- git
   - can be replaced by downloading ZIP archive of the repository


## Installation
```bash
git clone https://github.com/LayerManager/layman.git
cd layman
# checkout the latest release in current branch
git checkout $(git describe --abbrev=0 --tags)
```


## Run
There are following ways how to run Layman:
- [demo](#run-demo): the easiest and recommended way how to start layman for demonstration purposes 
- [development](#run-in-development): run layman in development mode
- [test](#test): run automatic tests
- [production](#run-in-production): run layman in production, requires installation of [external dependencies](#dependencies) and manual [configuration](#configuration)


## Run demo
This is the easiest way how to start layman for demonstration purposes. It includes also [external dependencies](#dependencies). However it's not meant for production and it's **not safe** for production. Performance might be also an issue.

```bash
# use demo settings
cp .env.demo .env

# start dockerized containers in background
make start-demo-full
```
Initial startup may take few minutes (download docker images, build it, run it). You are interested in container named `layman`. You can check its logs with command
```bash
docker logs -f layman
```
Wait until you see something like
```

[2019-10-30 13:45:36 +0000] [12] [INFO] Layman successfully started!
```

Then visit [http://localhost/](http://localhost/). You will see simple web client that interacts with [REST API](doc/rest.md). To check if Layman is running, call [GET Version](doc/rest.md#get-version).

To stop running service, run `make stop-demo`.


### Run demo with authentication

By default, demo starts without [authentication provider](doc/security.md#authentication). You can publish layers and maps as anonymous user, but you can't log in nor publish any private data.

To be able to use authentication and publish private data, follow these steps:
- Stop demo instance by `make stop-demo`
- Copy all  `OAUTH_*` environment variables from `.env.dev` to `.env` file.
- In `.env` change environment variables:
  ```
  LAYMAN_AUTHN_MODULES=layman.authn.oauth2,layman.authn.http_header
  OAUTH2_CALLBACK_URL=http://localhost/client/authn/oauth2-provider/callback
  ```
- Start demo with `make start-demo-full-with-optional-deps`

Then you can log in with automatically provided Wagtail user `layman` and password `laymanpwd`.

## Configuration
Layman's source code provides settings suitable for development, testing and demo purposes. Furthermore, there exists [`Makefile`](Makefile) with predefined commands for each purpose including starting all necessary services (both in background and foreground) and stoping it.

Layman's configuration is split into three levels:
- `docker-compose.*.yml` files used as [docker-compose configuration files](https://docs.docker.com/reference/compose-file/) with most general settings of docker containers including volume mappings, port mappings, container names and startup commands
- `.env*` files with environment settings of both build stage and runtime of docker containers
- `src/layman_settings.py` Python module with settings of Layman's Python modules for runtime

Files at all three levels are suffixed with strings that indicates what they are intended to:
- `demo` to [demonstration purposes](#run-demo)
- `dev` to [development](#run-in-development)
- `test` to [automatic tests](#test)
- `deps` to [external dependencies](#dependencies)

When you are switching between different contexts (e.g. between demo and dev), always check that you are using settings intended for your context, especially
- `.env*` file (check `env_file` properties in `docker-compose.*.yml` file)

Also, anytime you change `.env` file, remember to rebuild docker images as some environment variables affect build stage of docker images. Rebuild happens automatically as a part of `make start-demo*` commands.


## Dependencies
Layman has [many dependencies](doc/dependencies.md). Most of them are shipped with Layman. However, there are some **external dependencies** that should be treated carefully:
- PostgreSQL & PostGIS
- QGIS Server
- GeoServer
- Redis
- Micka

These external dependencies are shipped with Layman for development, testing and demo purposes. They are grouped in `docker-compose.deps*.yml` files.

However, if you want to run Layman in production, it is strongly recommended to install external dependencies separately. Recommended (i.e. tested) versions are:
- PostgreSQL 13.3 & PostGIS 3.1
- QGIS Server 3.16.1
- GeoServer 2.21.2
- Redis 4.0
- Micka 2020.014 (versions >=2020.010 probably work too)


## Upgrade
Layman follows [semantic versioning](https://semver.org/), so any change in MINOR and PATCH version should be backwards compatible. Still, human make mistakes, so it's recommended to backup data directories as a part of each upgrade.

General steps to upgrade layman to MINOR or PATCH version:
1. Stop layman. For demo configuration, `make stop-demo`, for dev configuration `make stop-dev`.
1. Backup data directories. By default, they are located at
   - `layman_data`
   - `deps/*/data` (data directories of external dependencies)
1. Follow **Upgrade requirements** in [Changelog](CHANGELOG.md) of all MINOR and PATCH versions greater than your current version and lower or equal to the version you are upgrading to.
   - If you run Layman in development mode (e.g. by `make start-dev`), run also
      - `make build-dev`
      - `make client-build`
      - `make timgen-build`
      - `make wagtail-build`
      - `make micka-build`
1. If you are expecting long-running upgrade, run **standalone upgrade**, otherwise Gunicorn could time out. The command depends on how you are starting Layman.
   - If you are starting Layman with `make start-demo`, run `make upgrade-demo`.
   - If you are starting Layman with `make start-demo-full` or `make start-demo-full-with-optional-deps`, run `make upgrade-demo-full`.
   - If you are starting Layman with `make start-dev`, you don't need to run standalone migration.
1. Start Layman.
> **_NOTE:_** If upgrade failed due to timeout of request to GeoServer, run `make upgrade-after-timeout` to finish upgrade.
> **_NOTE:_** If you run in problems during upgrade process, especially before v1.12.0, you can try to upgrade gradually through individual minor versions.

## Run in production
To run layman in production, you need to provide [external dependencies](#dependencies) and [configure](#configuration) layman manually.

When providing **external dependencies**, check their production-related documentation:
- [PostgreSQL 13.3](https://www.postgresql.org/docs/13/admin.html) & [PostGIS 3.1](http://postgis.net/docs/manual-3.1/performance_tips.html)
- [QGIS Server 3.16.1](https://docs.qgis.org/3.10/en/docs/user_manual/working_with_ogc/server/index.html)
- [GeoServer 2.21.2](https://geoserver.org/release/2.21.2/)
- [Redis 4.0](https://redis.io/docs/latest/operate/oss_and_stack/management/admin/)
- [Micka v2020.014](https://github.com/hsrs-cz/Micka/releases/tag/v2020.014), see also [configuration](deps/micka/sample/confs/config.local.neon) of [dockerized Micka](https://github.com/LayerManager/docker-micka).

Within PostgreSQL, you need to provide one database for Layman and one database for Micka. For Layman, you also need to provide one user [LAYMAN_PG_USER](doc/env-settings.md#LAYMAN_PG_USER) who needs enough privileges to create new schemas in [LAYMAN_PG_DBNAME](doc/env-settings.md#LAYMAN_PG_DBNAME) database. The user also needs access to `public` schema where PostGIS must be installed.

If you are using other DB schema than [internal role service schema](doc/security.md#internal-role-service-schema) as [role service](doc/security.md#role-service), you need to provide all [admin records](doc/security.md#admin-role-service-records).

Within QGIS Server, you do not need to provide anything special.

Within GeoServer, you need to provide either admin password [GEOSERVER_ADMIN_PASSWORD](doc/env-settings.md#GEOSERVER_ADMIN_PASSWORD), or one Layman user [LAYMAN_GS_USER](doc/env-settings.md#LAYMAN_GS_USER). If admin password is provided, Layman will create the Layman user automatically. URL path of the GeoServer must be `/geoserver/`.

Within Redis, you need to provide two databases, one for Layman, second for Layman Test Client. Connection strings are defined by [LAYMAN_REDIS_URL](doc/env-settings.md#LAYMAN_REDIS_URL) and [LTC_REDIS_URL](doc/env-settings.md#LTC_REDIS_URL).

Within Micka, you need to provide one user with editor privileges, whose credentials are defined by [CSW_BASIC_AUTHN](doc/env-settings.md#CSW_BASIC_AUTHN).

After providing external dependencies there is time to provide **internal dependencies** (system-level, python-level and node.js-level dependencies). You can either use our docker and docker compose configuration to generate docker images that already provides internal dependencies, or you can provide internal dependencies by yourself (if you prefer not to use docker in production).

**System-level** dependencies includes
- python 3.8+
- [python3-lxml](https://lxml.de/installation.html)
- [ogr2ogr](https://gdal.org/en/stable/programs/ogr2ogr.html) utility of [gdal](https://gdal.org/) 3.3+
- [chromium-browser](https://www.chromium.org/) 90+ and corresponding version of [chromedriver](https://developer.chrome.com/docs/chromedriver/)
- [pipenv](https://pypi.org/project/pipenv/)
- [node.js](https://nodejs.org/) 18 & npm 8 for running Layman Test Client
- [node.js](https://nodejs.org/) 16 & npm 8 for running Timgen

Pipenv is recommended tool for installing **python-level** dependencies. Both Pipfile and Pipfile.lock are located in [`docker/`](docker/) directory.

Npm is recommended tool for installing **node.js-level** dependencies. Both package.json and package-lock.json are located in [`timgen/`](timgen/) directory.

Next you need to choose how you deploy Layman. As Layman is Flask application, check Flask's [deployment options](https://flask.palletsprojects.com/en/2.3.x/deploying/). Layman is safe to run with multiple WSGI Flask processes and with multiple Celery worker processes.

Configure Layman using [environment settings](doc/env-settings.md). Demo configuration is a good starting point to setup Layman for production, however it needs to be adjusted carefully.

Last, start layman and necessary services:
- thumbnail image generator (Timgen) using npm (see startup command of `timgen` docker compose service)
- Layman client using npm (see startup command of `layman_client` docker compose service)
- Layman using your deployment server (see startup command of `layman` docker compose service)
- Layman celery worker using python (see startup command of `celery_worker` docker compose service)

## Run in development
Suitable for **development only**.

Before the first run:
```bash
# use dev settings
cp .env.dev .env

```

Now everything is ready to start:
```bash
# start all needed dockerized containers 
make start-dev
```
Initial startup may take few minutes (download docker images, build it, run it). Wait until you see something like
```
[2020-12-13 09:57:00,968] INFO in __init__: Layman successfully started!
```
in log of `layman_dev` container:
```bash
# see logs from Layman 
docker logs -f layman_dev
```

Then visit [http://localhost:8000/](http://localhost:8000/). You will see simple web client that interacts with [REST API](doc/rest.md). You can also log in with automatically provided Wagtail user `layman` and password `laymanpwd`.

To stop running service run:
```bash
# stop all needed dockerized containers 
make stop-dev
```



### Mount some volumes as non-root user
By default, docker run all containers as **root** user. It's possible to change it by defining `UID_GID` permanent environment variable. First stop all running containers:
```bash
make stop-dev 
```
The `UID_GID` variable should look like `"<user id>:<group id>"` of current user, e.g. `UID_GID="1000:1000"`. As it should be permanent, you can solve it for example by adding following line to your `~/.bashrc` file:
```
export UID_GID="1000:1000"
```
and restart terminal. Verification:
```bash
$ echo $UID_GID
1000:1000
```
Then change ownership of some directories
```bash
make prepare-dirs
sudo chown -R 1000:1000 layman_data/
sudo chown -R 1000:1000 layman_data_test/
sudo chown -R 1000:1000 src/
sudo chown -R 1000:1000 tmp/
```
and restart layman
```bash
make start-dev
```


## Test
:warning: It will delete
- all files within [LAYMAN_DATA_DIR](doc/env-settings.md#LAYMAN_DATA_DIR)!
- all files within [LAYMAN_QGIS_DATA_DIR](doc/env-settings.md#LAYMAN_QGIS_DATA_DIR)!
- all files within [LAYMAN_GS_NORMALIZED_RASTER_DIRECTORY](doc/env-settings.md#LAYMAN_GS_NORMALIZED_RASTER_DIRECTORY)!
- all layman-related schemas in [LAYMAN_PG_DBNAME](doc/env-settings.md#LAYMAN_PG_DBNAME)!
- database [EXTERNAL_DB_NAME](tests/__init__.py) and user [READ_ONLY_USER](tests/__init__.py)
- all workspaces and Layman users in [GeoServer](doc/data-storage.md#geoserver)!
- all keys in Redis logical database identified by [LAYMAN_REDIS_URL](doc/env-settings.md#LAYMAN_REDIS_URL)!
- all keys in Redis logical database identified by [LTC_REDIS_URL](doc/env-settings.md#LTC_REDIS_URL)!
- metadata records from CSW identified by [CSW_URL](doc/env-settings.md#CSW_URL) whose at least one online distribution URL contains [LAYMAN_PROXY_SERVER_NAME](doc/env-settings.md#LAYMAN_PROXY_SERVER_NAME)!

Default values are defined in [.env.test](.env.test)
```bash
# test related mainly to REST API endpoints of layers and maps
make test-static
make test-separated

# other tests
make test
```

For more information about tests, look at [test-related documentation for developers](tests/README.md).
