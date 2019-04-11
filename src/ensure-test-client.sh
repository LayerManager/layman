#!/bin/bash

if [ ! -d src/layman/static/test-client ]; then
    mkdir -p src/layman/static/test-client
    cd src/layman/static/test-client
    curl -L https://github.com/jirik/gspld-test-client/releases/download/v0.7.0/release.tar.gz | tar xvz
    cd ../../../../
fi
