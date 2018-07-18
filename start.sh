#!/bin/bash

find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
python3 src/prepare_layman.py && flask run --host=0.0.0.0 --port=8000