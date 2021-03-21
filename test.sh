#!/bin/bash

set -ex

bash src/clear-python-cache.sh

mkdir -p tmp/artifacts
rm -rf tmp/artifacts/*

#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xvv
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning --capture=tee-sys -xvv src/layman/gs_wfs_proxy_test.py
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/layer/client_test.py
python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/*_test.py


