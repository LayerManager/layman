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

# visit http://localhost:8000/

# stop it with Ctrl+C
```

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
- GeoServer 2.13.0
- PostgreSQL 10.0
- PostGIS 2.4

TODO: describe requirements on PostgreSQL and GeoServer user, privileges, etc.

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
cp .env.production .env

# edit .env
# edit src/layman/settings.py

# start dockerized layman & geoserver & DB
make start-layman-production-with-dbgeoserver

# visit http://localhost:8000/
```

