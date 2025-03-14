#!/bin/bash

set -ex

bash src/clear-python-cache.sh

mkdir -p tmp/artifacts
rm -rf tmp/artifacts/*

python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xvv tests/static_data/single_publication/layers_files_test.py::test_raster_files[test_workspace-layman.layer-post_jp2]
#python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -sxvv --capture=tee-sys tests/static_data
