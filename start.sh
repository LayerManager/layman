#!/bin/bash

bash src/clear-python-cache.sh

python3 src/wait_for_deps.py && flask run --host=0.0.0.0 --port=8000 "$@"