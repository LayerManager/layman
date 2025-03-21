#!/bin/bash

set -ex

bash src/clear-python-cache.sh

mkdir -p tmp/artifacts
rm -rf tmp/artifacts/*

max_fail="$1"
if [ -z "$max_fail" ]; then max_fail=1; fi

python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning --maxfail="$max_fail" -xvv --ignore=tests/static_data/ tests/dynamic_data/publications/layer_timeseries/timeseries_test.py::TestLayer::test_timeseries_layer
#python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m TEST_TYPE=optional pytest -W ignore::DeprecationWarning -sxvv --capture=tee-sys --nocleanup --ignore=tests/static_data/ tests
