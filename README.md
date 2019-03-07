# gspld [![Build Status](https://travis-ci.org/jirik/gspld.svg?branch=master)](https://travis-ci.org/jirik/gspld)
Publishing geospatial vector data online through [REST API](doc/rest.md).
- Accepts SHP and GeoJSON data files and SLD styles for visualization
- Even large files can be uploaded from browser
- Asynchronous upload and processing
- Provides URL endpoints:
  - WMS (powered by GeoServer)
  - WFS (powered by GeoServer)
  - thumbnail
- And other internal sources:
  - input file saved in file system
  - DB table with imported input file
- Everything is automatically named and structured first by user name, second by layer name
  - [REST API](doc/rest.md): `/rest/<username>/layers/<layername>` 
  - file system: `/path/to/LAYMAN_DATA_DIR/users/<username>/layers/<layername>` 
  - DB: `db=LAYMAN_PG_DBNAME, schema=<username>, table=<layername>` 
  - WMS/WFS: `/geoserver/<username>/ows, layer=<layername>, style=<layername>` 
- Simple rules
  - one DB table per input file
  - one WMS layer per DB table
  - one WFS feature type per DB table
  - one SLD style per WMS layer
- Configurable by environment variables
- Standing on the shoulders of Docker, Python, Flask, PostgreSQL, PostGIS, GDAL, GeoServer, Celery, Redis, and [more](doc/dependencies.md).

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
git clone https://github.com/jirik/gspld.git
cd gspld

# prepare geoserver data directory
make reset-layman-gs-datadir-production
```

## Run
Suitable for development only.
```bash
# start dockerized layman, geoserver, postgresql, redis, celery worker, and flower 
make start-layman-dev
```
Initial startup takes few minutes (download docker images, build it, run it). Wait until you see something like
```
layman       |  * Serving Flask app "src/layman/layman.py" (lazy loading)
layman       |  * Environment: development
layman       |  * Debug mode: on
layman       |  * Running on http://0.0.0.0:8000/ (Press CTRL+C to quit)
layman       |  * Restarting with stat
layman       |  * Debugger is active!
layman       |  * Debugger PIN: 103-830-055
```
Then visit [http://localhost:8000/](). You will see simple HTML form that enables to publish vector data file as new layer of WMS and WFS using [REST API](doc/rest.md). The form is for testing purpose only, the REST API is for production.

To stop running service, press Ctrl+C.

## Configuration
TLDR: Default settings are suitable for developemnt and testing (`make start-layman-dev` and `make test` commands). If you run it in production, manual configuration is needed.

The most general configuration is found in `docker-compose.*.yml` files used as [docker-compose configuration files](https://docs.docker.com/compose/compose-file/compose-file-v2/).
- `docker-compose.dev.yml` used for development
- `docker-compose.test.yml` used for automatic testing
- `docker-compose.production.yml` used for production (layman, redis, celery worker, flower)
- `docker-compose.dependencies.yml` optionally used for production (GeoServer and PostgreSQL)

Another part of settings is in `.env.*` files, also separate for development, testing, and production. See especially Layman settings and Flask settings. Remember layman is dockerized, so connection parameters such as host names and port numbers must be set according to docker-compose configuration. These settings are brought to python and extended by [settings.py](src/layman/settings.py).

## Test
:warning: It will delete
- all files within LAYMAN_DATA_DIR!
- all layman-related schemas in LAYMAN_PG_DBNAME!
- all workspaces accessible namely by LAYMAN_GS_ROLE!

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

Within GeoServer, you need one Layman user [LAYMAN_GS_USER](.env.production) and one layman role [LAYMAN_GS_ROLE](.env.production). **The LAYMAN_GS_USER must be another user than default `admin` user and the LAYMAN_GS_ROLE must be another role than default `ADMIN` role!** The user must have at least the LAYMAN_GS_ROLE and admin role. See [default development configuration](sample/geoserver_data/security/role/default/roles.xml).

```bash
cp .env.production .env

# edit .env
# edit src/layman/settings.py

# start dockerized layman only
make start-layman-production
```

## Run in production with dependencies
If you don't have existing GeoServer & PostGIS instance, you can use dockerized versions. It's easy to setup, but default settings are not safe for production. Performance might be also an issue.
```bash
# edit docker-compose.production.yml, e.g. to add geoserver_data volume
# prepare geoserver data directory
make reset-layman-gs-datadir

cp .env.production-and-deps .env

# edit .env, at least add FLASK_SECRET_KEY
# edit src/layman/settings.py

# start dockerized layman & geoserver & DB
make start-layman-production-with-dependencies

# visit http://localhost:8000/
```

