#!/bin/bash

set -exu

rm -rf tmp/artifacts/migration_to_v2_0_tests

# activate python virtual environment, set environment variables
source .venv/bin/activate
set -o allexport && source .env && set +o allexport

# run migrated data tests
PYTHONPATH=".:migration_to_v2_0_tests:src" python3 -m pytest -W ignore::DeprecationWarning -xvv migration_to_v2_0_tests/tests/

deactivate
