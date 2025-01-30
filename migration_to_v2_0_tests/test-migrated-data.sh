#!/bin/bash

set -exu

# activate python virtual environment, set environment variables
source .venv/bin/activate
set -o allexport && source .env && set +o allexport

# run migrated data tests
PYTHONPATH=".:tmp/migration_to_v2_0_tests:src" python3 -m pytest -W ignore::DeprecationWarning -xvv tmp/migration_to_v2_0_tests/tests/

deactivate
