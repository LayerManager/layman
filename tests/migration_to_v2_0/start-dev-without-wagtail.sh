#!/bin/bash

set -exu

mkdir -p layman_data layman_data_test tmp deps/qgis/data
docker compose -f docker-compose.deps.yml -f docker-compose.dev.yml up -d postgresql
docker compose -f docker-compose.deps.yml -f docker-compose.dev.yml run --rm --no-deps -u root layman_dev bash -c "cd src && python3 -B setup_geoserver.py"
docker compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --force-recreate -d layman_dev celery_worker_dev flower timgen layman_client postgresql qgis nginx-qgis geoserver redis micka

docker logs -f layman_dev 2>&1 | sed '/Layman successfully started/ q'
