#!/bin/bash

set -ex

bash src/clear-python-cache.sh

mkdir -p tmp/artifacts
rm -rf tmp/artifacts/*

python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xvv
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning --capture=tee-sys -xsvv src/layman/common/prime_db_schema/schema_initialization_test.py::test_recreate_schema
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning --capture=tee-sys -xsvv src/layman/common/prime_db_schema/schema_initialization_test.py src/layman/common/prime_db_schema/publications_test.py src/layman/common/prime_db_schema/users_test.py src/layman/common/prime_db_schema/workspaces_test.py
##python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning --capture=tee-sys -xsvv src/layman/common/prime_db_schema/publications_test.py
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning --capture=tee-sys -xsvv src/layman/common/prime_db_schema/users_test.py
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning --capture=tee-sys -xsvv src/layman/util_test.py::test_source_methods


