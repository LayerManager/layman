#!/bin/bash

set -exu

# activate python virtual environment, set environment variables
source .venv/bin/activate
set -o allexport && source .env && set +o allexport

# publish some layers on Layman 1.23.x
PYTHONPATH=".:tmp/migration_to_v2_0:src" python tmp/migration_to_v2_0/prepare_data_on_v1_23.py

deactivate
