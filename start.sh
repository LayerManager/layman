#!/bin/bash

bash src/clear-python-cache.sh


# when using non-root user in docker container, flask reloader is not working
#python3 src/wait_for_deps.py && flask run --host=0.0.0.0 --port=8000 "$@"

# therefore use watchmedo
python3 src/layman_flush_redis.py && python3 src/wait_for_deps.py && watchmedo auto-restart -d ./src -p '*.py' --recursive -- flask run --host=0.0.0.0 --port=8000 --no-reload