#!/bin/bash

set -ex

if [ ! -f /app/data/db.sqlite3 ]; then
    echo "File db.sqlite3 not found, copying the default one."
    cp /app/initial_data/db.sqlite3 /app/data/
fi

exec waitress-serve --listen "*:8000" "laymanportal.wsgi:application"
