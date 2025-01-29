#!/bin/bash

set -exu

# remember current git branch and switch to Layman 1.23.x
make stop-and-remove-all-docker-containers
git rev-parse --abbrev-ref HEAD > tmp/migration_to_v2_0/current-v2-git-branch.txt
git stash clear
git stash
git fetch
git checkout 1.23.x
git pull
cp .env.dev .env
sed -i -e "s/OAUTH2_INTROSPECTION_URL=.*/OAUTH2_INTROSPECTION_URL=http:\\/\\/host.docker.internal:8123\\/rest\\/test-oauth2\\/introspection?is_active=true/" .env
sed -i -e "s/OAUTH2_USER_PROFILE_URL=.*/OAUTH2_USER_PROFILE_URL=http:\\/\\/host.docker.internal:8123\\/rest\\/test-oauth2\\/user-profile/" .env
sed -i -e "s/FLASK_SECRET_KEY=.*/FLASK_SECRET_KEY=fb8727f383cacdbdcbf74d2f878b4141b15109f02cbe6117bb7d95605aa1f46f/" .env
sed -i -e '/   layman_dev/a\' -e '      extra_hosts:\n         - "host.docker.internal:host-gateway"' docker-compose.dev.yml
sed -i -e '/   celery_worker_dev/a\' -e '      extra_hosts:\n         - "host.docker.internal:host-gateway"' docker-compose.dev.yml
docker pull layermanager/layman:dev-1-23
docker tag layermanager/layman:dev-1-23 layman_dev
docker pull layermanager/layman:client-1-23
docker tag layermanager/layman:client-1-23 layman_client
docker tag layermanager/layman:client-1-23 layman_client_test
docker pull layermanager/layman:timgen-1-23
docker tag layermanager/layman:timgen-1-23 timgen
docker compose --compatibility -f docker-compose.deps.yml -f docker-compose.dev.yml pull redis postgresql
docker compose --compatibility -f docker-compose.deps.yml -f docker-compose.dev.yml build geoserver
make micka-build && make qgis-build

make reset-data-directories
