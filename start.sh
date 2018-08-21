#!/bin/bash

bash src/clear-python-cache.sh

bash src/ensure-test-client.sh

python3 src/prepare_layman.py && flask run --host=0.0.0.0 --port=8000