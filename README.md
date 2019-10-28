# layman
[![Build Status](https://travis-ci.org/jirik/layman.svg?branch=master)](https://travis-ci.org/jirik/layman)

Publishing geospatial data online through [REST API](doc/rest.md).

- Two publication models available:
  - [**layer**](doc/models.md#layer): visual representation of single vector dataset (i.e. ShapeFile or GeoJSON)
  - [**map**](doc/models.md#layer): collection of layers
- Accepts data in [GeoJSON](https://en.wikipedia.org/wiki/GeoJSON), [ShapeFile](https://en.wikipedia.org/wiki/Shapefile), [Styled Layer Descriptor](https://www.opengeospatial.org/standards/sld), [Symbology Encoding](https://www.opengeospatial.org/standards/se), or [HSLayers Map Composition](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema) format
- Even large files can be easily uploaded from browser thanks to asynchronous chunk upload
- Asynchronous processing
- Each vector dataset is automatically imported into PostGIS database
- Provides URL endpoints
  - [Web Map Service (WMS)](https://www.opengeospatial.org/standards/wms)
  - [Web Feature Service (WFS)](https://www.opengeospatial.org/standards/wfs)
  - thumbnail image
- Documented [REST API](doc/rest.md)
- Documented [security system](doc/security.md)
- Documented [data storage](doc/data-storage.md)
- Configurable by environment variables
- Standing on the shoulders of Docker, Python, Flask, PostgreSQL, PostGIS, GDAL, GeoServer, OpenLayers, Celery, Redis, and [more](doc/dependencies.md)
- Inspired by [CCSS-CZ/layman](https://github.com/CCSS-CZ/layman)


## Requirements
- at least 3 GB RAM
- at least 5 GB disk space
- docker v17.12+, installation instructions for [centos 7](https://docs.docker.com/install/linux/docker-ce/centos/)
- docker-compose v1.14+, installation instructions for [centos 7](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-centos-7)

**Optionally**
- linux or any tool to run tasks defined in Makefile using `make` command
   - can be replaced by running commands defined in [Makefile](Makefile) directly
- git
   - can be replaced by downloading ZIP archive of the repository


## Installation
```bash
git clone https://github.com/jirik/layman.git
cd layman
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
cp src/layman_settings_demo.py src/layman_settings.py

# prepare GeoServer data directory with appropriate configuration for Layman
make geoserver-reset-default-layman-datadir

# start dockerized containers
make start-demo
```
Initial startup may take few minutes (download docker images, build it, run it). Wait until you see something like
```
layman       |  * Serving Flask app "src/layman"
layman       |  * Environment: production
layman       |    WARNING: This is a development server. Do not use it in a production deployment.
layman       |    Use a production WSGI server instead.
layman       |  * Debug mode: off
layman       |  * Running on http://0.0.0.0:8000/ (Press CTRL+C to quit)
```

Then visit [http://localhost:8000/](). You will see simple web client that interacts with [REST API](doc/rest.md).

To stop running service, press Ctrl+C.

You can start Layman also in background with `make start-demo-d` (`d` for detached), and stop it with `stop-demo`.


## Configuration
Layman's source code provides settings suitable for development, testing and demo purposes. Furthermore, there exists [`Makefile`](#Makefile) with predefined commands for each purpose including starting all necessary services (both in background and foreground) and stoping it.

Layman's configuration is split into three levels:
- `docker-compose.*.yml` files used as [docker-compose configuration files](https://docs.docker.com/compose/compose-file/compose-file-v3/) with most general settings of docker containers including volume mappings, port mappings, container names and startup commands
- `.env*` files with environment settings of both build stage and runtime of docker containers
- `src/layman_settings*.py` Python modules with settings of Layman's Python modules for runtime

Files at all three levels are suffixed with strings that indicates what they are intended to:
- `demo` to [demonstration purposes](#run-demo)
- `dev` to [development](#run-in-development)
- `test` to [automatic tests](#test)
- `deps` to [external dependencies](#dependencies)

When you are switching between different contexts (e.g. between demo and dev), always check that you are using settings intended for your context, especially
- `.env*` file (check `env_file` properties in )
- `layman_settings*` file (check `LAYMAN_SETTINGS_MODULE` environment variable in `env*` file)

Also, anytime you change `.env` file, remember to rebuild docker images as some environemnt variables affect build stage of docker images. Particularly these environment settings:
- UID_GID
- LAYMAN_GS_HOST
- LAYMAN_GS_PORT
- LAYMAN_DOCKER_MAIN_SERVICE
- LAYMAN_CLIENT_VERSION


## Dependencies
Layman has [many dependencies](doc/dependencies.md). Most of them is shipped with Layman. However there are some **external dependencies** that should be treated carefully:
- PostgreSQL & PostGIS
- GeoServer
- Redis

These external dependencies are shipped with Layman for development, testing and demo purposes. They are grouped in `docker-compose.deps*.yml` files.

However, if you want to run Layman in production, it is strongly recommended to install external dependencies separately. Recommended (i.e. tested) versions are:
- PostgreSQL 10.0 & PostGIS 2.4
- GeoServer 2.13.0
- Redis 4.0

Within PostgreSQL, you need to provide one user [LAYMAN_PG_USER](doc/env-settings.md#LAYMAN_PG_USER) who needs enough privileges to create new schemas in [LAYMAN_PG_DBNAME](doc/env-settings.md#LAYMAN_PG_DBNAME) database. The user also needs access to `public` schema where PostGIS must be installed.

Within GeoServer, you need to provide one Layman user [LAYMAN_GS_USER](doc/env-settings.md#LAYMAN_GS_USER) and one layman role [LAYMAN_GS_ROLE](doc/env-settings.md#LAYMAN_GS_ROLE).

Within Redis, you need to provide two databases, one for Layman, second for Layman Test Client. Connection strings are defined by [LAYMAN_REDIS_URL](doc/env-settings.md#LAYMAN_REDIS_URL) and [LTC_REDIS_URL](doc/env-settings.md#LTC_REDIS_URL).


## Run in production
To run layman in production, you need to provide [external dependencies](#dependencies) and [configure](#configuration) layman manually.

When providing external dependencies, check their production-related documentation:
- [PostgreSQL 10.0](https://www.postgresql.org/docs/10/admin.html) & [PostGIS 2.4](http://postgis.net/docs/manual-2.4/performance_tips.html)
- [GeoServer 2.13.0](https://docs.geoserver.org/2.13.0/user/production/index.html#production)
- [Redis 4.0](https://redis.io/topics/admin)

After providing external dependencies there is time to provide **internal dependencies** (system-level, python-level and node.js-level dependencies). You can either use our docker and docker-compose configuration to generate docker images that already provides internal dependencies, or you can provide internal dependencies by you self (if you prefer not to use docker in production).

**System-level** dependencies includes
- python 3.6+
- [ogr2ogr](https://gdal.org/programs/ogr2ogr.html) utility of [gdal](https://gdal.org/) 2.4+
- [chromium-browser](https://chromium.org/) 77
- [chromedriver](https://chromedriver.chromium.org/) 77
- [pipenv](https://pipenv.kennethreitz.org/en/latest/)
- [node.js](https://nodejs.org/) 10+ & npm

Pipenv is recommended tool for installing **python-level** dependencies. Both Pipfile and Pipfile.lock are located in [`docker/`](#docker/) directory.

Npm is recommended tool for installing **node.js-level** dependencies. Both package.json and package-lock.json are located in [`hslayers/`](#hslayers/) directory.

Next you need to choose how you deploy Layman. As Layman is a Flask application, check Flask's [deployment options](https://flask.palletsprojects.com/en/1.1.x/deploying/). Keep in mind that Flask is safe to run with **one process** only.

Configure Layman using [environment settings](doc/env-settings.md). First focus for example on
- LAYMAN_SETTINGS_MODULE
- FLASK_ENV (should be set to `production`)
- LTC_SESSION_SECRET
- FLASK_SECRET_KEY

Demo configuration is a good starting point to setup Layman for production, however it needs to be adjusted carefully.

Last, start layman and necessary services:
- hslayers using npm
- layman client using npm
- layman using you deployment server
- celery worker using python

## Run in development
Suitable for **development only**.

Before the first run:
```bash
# prepare geoserver data directory
make geoserver-reset-default-layman-datadir

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
layman       |  * Serving Flask app "src/layman/layman.py" (lazy loading)
layman       |  * Environment: development
layman       |  * Debug mode: on
layman       |  * Running on http://0.0.0.0:8000/ (Press CTRL+C to quit)
layman       |  * Restarting with stat
layman       |  * Debugger is active!
layman       |  * Debugger PIN: 103-830-055
```
Then visit [http://localhost:8000/](). You will see simple web client that interacts with [REST API](doc/rest.md).

To stop running service, press Ctrl+C.


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
sudo chown -R 1000:1000 src/layman/static/test-client/
```
and restart layman
```bash
make start-dev
```


## Test
:warning: It will delete
- all files within LAYMAN_DATA_DIR!
- all layman-related schemas in LAYMAN_PG_DBNAME!
- all workspaces accessible namely by LAYMAN_GS_ROLE!
- all keys in Redis keyspace identified by LAYMAN_REDIS_URL!
- all keys in Redis keyspace identified by LTC_REDIS_URL!

Default values are defined in [.env.test](.env.test)
```bash
make test
```
