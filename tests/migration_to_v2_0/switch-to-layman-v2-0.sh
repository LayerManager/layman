#!/bin/bash

set -exu

make stop-and-remove-all-docker-containers || true
git checkout -- docker-compose.dev.yml

# switch to original branch of Layman 2.0
git checkout "$(<tmp/migration_to_v2_0/original-v2-git-branch.txt)"
git stash pop || true
cp .env.dev .env
sed -i -e "s/OAUTH2_INTROSPECTION_URL=.*/OAUTH2_INTROSPECTION_URL=http:\\/\\/host.docker.internal:8123\\/rest\\/test-oauth2\\/introspection?is_active=true/" .env
sed -i -e "s/OAUTH2_USER_PROFILE_URL=.*/OAUTH2_USER_PROFILE_URL=http:\\/\\/host.docker.internal:8123\\/rest\\/test-oauth2\\/user-profile/" .env
make pull-dev-images
docker compose -f docker-compose.deps.yml -f docker-compose.dev.yml pull redis postgresql nginx-qgis geoserver
make micka-build && make qgis-build
