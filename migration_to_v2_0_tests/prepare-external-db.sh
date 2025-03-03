#!/bin/bash

set -exu

docker compose -f docker-compose.deps.yml run -e PGPASSWORD=docker --entrypoint "psql -U docker -p 5432 -h postgresql gis -c 'CREATE DATABASE external_test_db TEMPLATE template_postgis'" --rm postgresql

docker compose -f docker-compose.deps.yml run -e PGPASSWORD=docker --entrypoint "psql -U docker -p 5432 -h postgresql external_test_db -c 'CREATE SCHEMA IF NOT EXISTS external_db_schema AUTHORIZATION docker'" --rm postgresql

docker compose -f docker-compose.dev.yml -f docker-compose.deps.yml run --rm --no-deps layman_dev bash -c "ogr2ogr -nln external_db_table -lco SCHEMA=external_db_schema -lco LAUNDER=NO -lco EXTRACT_SCHEMA_FROM_LAYER_NAME=NO -lco GEOMETRY_NAME=wkb_geometry -lco FID=ogc_fid -f PostgreSQL PG:\"host=postgresql port=5432 dbname=external_test_db user=docker password=docker\" sample/layman.layer/small_layer.geojson"
