#!/bin/bash

set -exu

# prepare virtual environment
./inspect_performance/prepare-venv.sh

make stop-and-remove-all-docker-containers || true
make reset-data-directories

# start Layman with oauth2_provider_mock authentication
cp .env.dev .env
sed -i -e "s/OAUTH2_INTROSPECTION_URL=.*/OAUTH2_INTROSPECTION_URL=http:\\/\\/host.docker.internal:8123\\/rest\\/test-oauth2\\/introspection?is_active=true/" .env
sed -i -e "s/OAUTH2_USER_PROFILE_URL=.*/OAUTH2_USER_PROFILE_URL=http:\\/\\/host.docker.internal:8123\\/rest\\/test-oauth2\\/user-profile/" .env
make start-dev
docker logs -f layman_dev 2>&1 | sed '/Layman successfully started/ q'

# inspect performance
source .venv/bin/activate
set -o allexport && source .env && set +o allexport

# prepare some data on Layman 1.23.x
PYTHONPATH=".:inspect_performance:src" python inspect_performance/run_inspect.py

deactivate

cp .env.dev .env
