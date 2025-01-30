#!/bin/bash

set -exu

# copy `tests/migration_to_v2_0` to `tmp` folder and prepare virtual environment
./tests/migration_to_v2_0/prepare-venv.sh

# remember original git branch and switch to Layman 1.23.x
./tmp/migration_to_v2_0/switch-to-layman-v1-23.sh

# start empty Layman 1.23.x
./tmp/migration_to_v2_0/start-dev-without-wagtail.sh

# publish test data on Layman 1.23.x
./tmp/migration_to_v2_0/publish-data-on-v1-23.sh

# switch to original branch of Layman 2.0
./tmp/migration_to_v2_0/switch-to-layman-v2-0.sh

# run standalone upgrade to Layman 2.0
make upgrade-dev

# start Layman 2.0
./tmp/migration_to_v2_0/start-dev-without-wagtail.sh

# run migrated data tests
./tmp/migration_to_v2_0/test-migrated-data.sh

## switch back to original v2 branch
#make stop-and-remove-all-docker-containers || true && git checkout -- docker-compose.dev.yml && git checkout "$(<tmp/migration_to_v2_0/original-v2-git-branch.txt)" && cp .env.dev .env && (git stash pop || true) && make pull-dev-images && make micka-build && make qgis-build && make reset-data-directories
