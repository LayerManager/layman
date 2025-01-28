#!/bin/bash

set -exu

# copy `tests/migration_to_v2_0` to folder ignored by git, so that `git checkout` won't affect it
rm -rf tmp/migration_to_v2_0
mkdir -p tmp
cp -r tests/migration_to_v2_0 tmp

# prepare python virtual environment to run python scripts on host (not in docker)
deactivate || true
# rm -rf .venv
cp docker/Pipfile .
python3 --version
CURRENT_PYTHON_VERSION="$(python3 --version | grep -oP 3\.[0-9]+)"
echo "CURRENT_PYTHON_VERSION = $CURRENT_PYTHON_VERSION"
pip3 --version
pip3 install --user pipenv
pipenv --version
sed -i -e 's/python_version = "3.8"/python_version = "'"$CURRENT_PYTHON_VERSION"'"/' Pipfile
PIPENV_VENV_IN_PROJECT=1 pipenv install --dev

# remember current git branch and switch to Layman 1.23.x
make stop-and-remove-all-docker-containers
CURRENT_GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "CURRENT_GIT_BRANCH = $CURRENT_GIT_BRANCH"
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
make micka-build && make qgis-build

# start empty Layman 1.23.x
make reset-data-directories
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
