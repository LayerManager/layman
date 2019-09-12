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
Suitable for **development only**.

Before the first run:
```bash
# use development settings
cp .env.dev .env

# prepare geoserver data directory
make geoserver-reset-default-layman-datadir
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
make stop-and-remove-dev 
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

## Configuration
TLDR: Default settings are suitable for development and testing (`make start-layman-dev` and `make test` commands). If you run it in production, manual configuration is needed.

The most general configuration is found in `docker-compose.*.yml` files used as [docker-compose configuration files](https://docs.docker.com/compose/compose-file/compose-file-v2/).
- `docker-compose.dev.yml` used for development
- `docker-compose.test.yml` used for automatic testing
- `docker-compose.production.yml` used for production (layman, celery worker, flower)
- `docker-compose.deps.yml` used for development, testing, and optionally for production (GeoServer, PostgreSQL, Redis)

Another part of settings is in `.env.*` files, also separately for development, testing, and production. See especially Layman settings and Flask settings. Remember layman is dockerized, so connection parameters such as host names and port numbers must be set according to docker-compose configuration.

Settings from `.env.*` are brought to python and extended by [layman_settings.py](src/layman_settings.py).

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

## Run standalone in production
This is the recommended way how to run it in production. You need to provide external PostGIS & GeoServer instances. Tested versions:
- PostgreSQL 10.0
- PostGIS 2.4
- GeoServer 2.13.0

Within PostgreSQL, you need one user [LAYMAN_PG_USER](.env.production) who needs enough privileges to create new schemas in [LAYMAN_PG_DBNAME](.env.production) database. **The LAYMAN_PG_USER must be another user than default `postgres` user!** The user also needs access to `public` schema where PostGIS must be installed.

Within GeoServer, you need one Layman user [LAYMAN_GS_USER](.env.production) and one layman role [LAYMAN_GS_ROLE](.env.production). **The LAYMAN_GS_USER must be another user than default `admin` user and the LAYMAN_GS_ROLE must be another role than default `ADMIN` role!** The LAYMAN_GS_USER user must have at least the LAYMAN_GS_ROLE and ADMIN role. See default development configuration of [roles](deps/geoserver/sample/geoserver_data/security/role/default/roles.xml) and [layer access rights](deps/geoserver/sample/geoserver_data/security/layers.properties).

```bash
cp .env.production .env

# edit .env
# edit docker-compose.production.yml
# edit src/layman_settings.py

# prepare geoserver data directory
make geoserver-reset-default-layman-datadir

# start dockerized containers
make start-layman-production

# visit http://localhost:8000/
```

## Run in production with dependencies
If you don't have existing GeoServer & PostGIS instance, you can use dockerized versions. It's easy to setup, but default settings are **not safe** for production. Performance might be also an issue.
```bash
cp .env.production-and-deps .env

# edit .env, at least add FLASK_SECRET_KEY

# prepare geoserver data directory
make geoserver-reset-default-layman-datadir

# start dockerized containers
make start-layman-production-with-dependencies

# visit http://localhost:8000/
```

