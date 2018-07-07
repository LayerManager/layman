# gspld
Publishing geospatial vector data online

## Requirements
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
```bash
# first start layman for development
# then continue with
make test
```

## Run standalone in production
If you have existing GeoServer & PostGIS instance:
```bash
cp .env.production .env

# edit .env

# start dockerized layman only
make start-layman-production
```

## Run in production with dependencies
If you don't have existing GeoServer & PostGIS instance:
```bash
cp .env.production .env

# edit .env

# start dockerized layman & geoserver & DB
make start-layman-production-with-dbgeoserver

# visit http://localhost:8000/
```

