# gspld [![Build Status](https://travis-ci.org/jirik/gspld.svg?branch=master)](https://travis-ci.org/jirik/gspld)
Publishing geospatial vector data online

## Requirements
- linux
- docker
- docker-compose


## Installation
```bash
git clone https://github.com/jirik/gspld.git
cd gspld

# prepare geoserver data directory
GS_VERSION=2.13.0 make download-gs-datadir
sudo GS_VERSION=2.13.0 make reset-gs-datadir
```

## Run
Suitable for development only.
```bash
# start dockerized layman & geoserver & DB
make start-layman-dev

# visit http://localhost:8000/
```

## Test
:warning: It will delete all files within LAYMAN_DATA_DIR and all layman-related schemas in LAYMAN_PG_DBNAME! Default values are defined in [.env.test](https://github.com/jirik/gspld/blob/master/.env.test)
```bash
make test
```

## Run standalone in production
If you have existing GeoServer & PostGIS instance:
```bash
cp .env.production .env

# edit .env
# edit src/layman/settings.py

# start dockerized layman only
make start-layman-production
```

## Run in production with dependencies
If you don't have existing GeoServer & PostGIS instance:
```bash
cp .env.production .env

# edit .env
# edit src/layman/settings.py

# start dockerized layman & geoserver & DB
make start-layman-production-with-dbgeoserver

# visit http://localhost:8000/
```

