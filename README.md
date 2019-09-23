# layman
[![Build Status](https://travis-ci.org/jirik/layman.svg?branch=master)](https://travis-ci.org/jirik/layman)

Publishing geospatial data online through [REST API](doc/rest.md).

- Two models available:
  - [**layer**](doc/models.md#layer): visual representation of single vector dataset (i.e. ShapeFile or GeoJSON)
  - [**map**](doc/models.md#layer): collection of layers
- Accepts data in [GeoJSON](https://en.wikipedia.org/wiki/GeoJSON), [ShapeFile](https://en.wikipedia.org/wiki/Shapefile), [Styled Layer Descriptor](https://www.opengeospatial.org/standards/sld), [Symbology Encoding](https://www.opengeospatial.org/standards/se), or [HSLayers Map Composition](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema) format
- Even large files can be uploaded from browser
- Asynchronous upload and processing
- Each vector dataset is automatically imported into PostGIS database
- Provides URL endpoints
  - [Web Map Service (WMS)](https://www.opengeospatial.org/standards/wms)
  - [Web Feature Service (WFS)](https://www.opengeospatial.org/standards/wfs)
  - thumbnail image
- Documented [REST API](doc/rest.md)
- Documented [security system](doc/security.md)
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
- [production](#run-in-production): run layman in production, requires installation of [external dependencies](#dependencies) and manual [configuration](#configuration)
- [development](#run-in-development): run layman in development mode
- [test](#test): just run automatic tests


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
Default settings are suitable for development, testing and demo purposes. If you run it in production, manual configuration is required.

The most general configuration is found in `docker-compose.*.yml` files used as [docker-compose configuration files](https://docs.docker.com/compose/compose-file/compose-file-v3/).
- `docker-compose.production.yml` used for production and demo purposes
- `docker-compose.deps.yml` [external dependencies](#dependencies) used for development, testing, and demo purposes
- `docker-compose.dev.yml` used for development
- `docker-compose.test.yml` used for automatic testing

Another part of settings is in `.env.*` files, separately for demo, production, development, and testing. See especially Layman settings and Flask settings. Remember layman is dockerized, so connection parameters such as host names and port numbers must be set according to docker-compose configuration.

Settings from `.env.*` are brought to python and extended by [layman_settings.py](src/layman_settings.py).


## Dependencies
Layman has [many dependencies](doc/dependencies.md). Most of them is shipped with layman. However there are some **external dependencies** that should be treated carefully:
- PostgreSQL & PostGIS
- GeoServer
- Redis
These external dependencies are shipped with Layman for development, testing and demo purposes. They are grouped in `docker-compose.deps.yml` file.

However, if you want to run Layman in production, it is strongly recommended to install external dependencies separately. Recommended (i.e. tested) versions are:
- PostgreSQL 10.0 & PostGIS 2.4
- GeoServer 2.13.0
- Redis 4.0

Within PostgreSQL, you need to provide one user [LAYMAN_PG_USER](.env.production) who needs enough privileges to create new schemas in [LAYMAN_PG_DBNAME](.env.production) database. **The LAYMAN_PG_USER must be another user than default `postgres` user!** The user also needs access to `public` schema where PostGIS must be installed.

Within GeoServer, you need to provide one Layman user [LAYMAN_GS_USER](.env.production) and one layman role [LAYMAN_GS_ROLE](.env.production). **The LAYMAN_GS_USER must be another user than default `admin` user and the LAYMAN_GS_ROLE must be another role than default `ADMIN` role!** The LAYMAN_GS_USER user must have at least the LAYMAN_GS_ROLE and ADMIN role. See default development configuration of [roles](deps/geoserver/sample/geoserver_data/security/role/default/roles.xml) and [layer access rights](deps/geoserver/sample/geoserver_data/security/layers.properties).

Within Redis, you need to provide one database. Connection string is defined by [LAYMAN_REDIS_URL](.env.production).


## Run in production
To run layman in production, you need to provide [external dependencies](#dependencies) and [configure](#configuration) layman manually, at least `.env` file:

```bash
# use production settings
cp .env.production .env
cp src/layman_settings_production.py src/layman_settings.py

# edit .env
# optionally edit docker-compose.production.yml
# optionally edit src/layman_settings.py

# prepare geoserver data directory
make geoserver-reset-default-layman-datadir

# start dockerized containers
make start-production

# visit http://localhost:8000/
```


## Run in development
Suitable for **development only**.

Before the first run:
```bash
# prepare geoserver data directory
make geoserver-reset-default-layman-datadir

# use dev settings
cp .env.demo .env

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

Default values are defined in [.env.test](.env.test)
```bash
make test
```
