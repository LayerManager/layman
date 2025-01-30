#!/bin/bash

set -exu

# activate python virtual environment, set environment variables
source .venv/bin/activate
set -o allexport && source .env && set +o allexport

# prepare some data on Layman 1.23.x
PYTHONPATH=".:tmp/migration_to_v2_0_tests:src" python tmp/migration_to_v2_0_tests/prepare_data_on_v1_23.py

deactivate
