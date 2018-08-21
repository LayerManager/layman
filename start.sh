#!/bin/bash

bash src/clear-python-cache.sh

if [ ! -d src/layman/static/test-client ]; then
    cd src/layman
    rm -rf static/test-client
    curl -L https://github.com/jirik/gspld-test-client/releases/download/v0.1/release.tar.gz | tar xvz
    cd ../../
fi

python3 src/prepare_layman.py && flask run --host=0.0.0.0 --port=8000