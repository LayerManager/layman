# gspld [![Build Status](https://travis-ci.org/jirik/gspld.svg?branch=master)](https://travis-ci.org/jirik/gspld)
Publishing geospatial vector data online

## Requirements
- linux (needed only for `make` commands)
- docker
- docker-compose


## Installation
```bash
git clone https://github.com/jirik/gspld.git
cd gspld

# prepare geoserver data directory
make reset-layman-gs-datadir
```

## Run
Suitable for development only.
```bash
# start dockerized layman & geoserver & DB
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
Then visit [http://localhost:8000/](). You will see simple HTML form that enables to publish vector data file as new layer of WMS and WFS using [REST API](https://github.com/jirik/gspld/blob/master/REST.md). The form is for testing purpose only, the REST API is for production.

To stop running service, press Ctrl+C.

## Configuration
TLDR: Default settings are suitable for developemnt and testing (`make start-layman-dev` and `make test` commands). If you run it in production, you manual configuration is needed.

The most general documentation is found in `docker-compose.*.yml` files used as [docker-compose configuration files](https://docs.docker.com/compose/compose-file/compose-file-v2/).
- `docker-compose.dev.yml` used for development
- `docker-compose.test.yml` used for automatic testing
- `docker-compose.production.yml` used for production (standalone layman)
- `docker-compose.dependencies.yml` used for production (GeoServer and PostgreSQL)

Another part of settings is in `.env.*` files, also separate for development, testing, and production. See especially Layman settings and Flask settings. Remember layman is dockerized, so connection parameters such as host names and port numbers must be set according to docker-compose configuration.

## Test
:warning: It will delete
- all files within LAYMAN_DATA_DIR!
- all layman-related schemas in LAYMAN_PG_DBNAME!
- all workspaces accessible namely by LAYMAN_GS_ROLE!

Default values are defined in [.env.test](https://github.com/jirik/gspld/blob/master/.env.test)
```bash
make test
```

## Run standalone in production
This is the recommended way how to run it in production. You need GeoServer & PostGIS instances. Tested versions:
- PostgreSQL 10.0
- PostGIS 2.4
- GeoServer 2.13.0

PostgreSQL user LAYMAN_PG_USER needs enough privileges to create new schemas in LAYMAN_PG_DBNAME database. **The LAYMAN_PG_USER must be another user than default `postgres` user!** The user also needs access to `public` schema where PostGIS must be installed.

Within GeoServer, you need one Layman user LAYMAN_GS_USER and one layman role LAYMAN_GS_ROLE. **The LAYMAN_GS_USER must be another user than default `admin` user and the LAYMAN_GS_ROLE must be another role than default `ADMIN` role!** The user must have at least the LAYMAN_GS_ROLE and admin role. See [default development configuration](https://github.com/jirik/gspld/blob/geoserver_setup/sample/geoserver_data/security/role/default/roles.xml).

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

cp .env.production .env

# edit .env
# edit src/layman/settings.py

# start dockerized layman & geoserver & DB
make start-layman-production-with-dependencies

# visit http://localhost:8000/
```

