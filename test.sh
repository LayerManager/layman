#!/bin/bash

set -ex

bash src/clear-python-cache.sh

mkdir -p tmp/artifacts
rm -rf tmp/artifacts/*

if [ "$CI" == "true" ]
then
  python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -m "not irritating" --timeout=60 -W ignore::DeprecationWarning -xvv src
else
  python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -m "not irritating" -W ignore::DeprecationWarning -xvv src
fi
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning --capture=tee-sys -xvv src/layman/gs_wfs_proxy_test.py
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/layer/client_test.py
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/layer/rest_test.py::test_post_layers_complex src/layman/layer/rest_test.py::test_patch_layer_data src/layman/layer/rest_test.py::test_patch_layer_concurrent_and_delete_it


