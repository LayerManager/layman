#!/bin/bash

python3 src/layman/prepare.py && flask run --host=0.0.0.0 --port=8000