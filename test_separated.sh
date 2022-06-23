#!/bin/bash

set -ex

bash src/clear-python-cache.sh

mkdir -p tmp/artifacts
rm -rf tmp/artifacts/*

python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && TEST_TYPE=mandatory python3 -m pytest -W ignore::DeprecationWarning -xvv tests
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m TEST_TYPE=optional pytest -W ignore::DeprecationWarning -sxvv --capture=tee-sys --nocleanup tests/dynamic_data/publication_test.py
