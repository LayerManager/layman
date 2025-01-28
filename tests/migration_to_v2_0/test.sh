#!/bin/bash

set -exu

# copy `tests/migration_to_v2_0` to `tmp` folder and prepare virtual environment
./tests/migration_to_v2_0/prepare-venv.sh

# remember current git branch and switch to Layman 1.23.x
source ./tmp/migration_to_v2_0/switch-to-layman-v1-23.sh

# start empty Layman 1.23.x
./tmp/migration_to_v2_0/start-dev-without-wagtail.sh

# activate python virtual environment, set environment variables
source .venv/bin/activate
set -o allexport && source .env && set +o allexport

# publish some layers on Layman 1.23.x
PYTHONPATH=".:tmp/migration_to_v2_0:src" python tmp/migration_to_v2_0/prepare_data_on_v1_23.py

# undo changes in files tracked by git
git checkout -- docker-compose.dev.yml

deactivate

# switch back to current branch
make stop-and-remove-all-docker-containers || true && git checkout -- docker-compose.dev.yml && git checkout $CURRENT_GIT_BRANCH && cp .env.dev .env && (git stash pop || true) && make pull-dev-images && make micka-build && make qgis-build && make reset-data-directories
