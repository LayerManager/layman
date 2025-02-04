#!/bin/bash

set -exu

# prepare python virtual environment to run python scripts on host (not in docker)
deactivate || true
# rm -rf .venv
cp docker/Pipfile .
python3 --version
CURRENT_PYTHON_VERSION="$(python3 --version | grep -oP 3\.[0-9]+)"
echo "CURRENT_PYTHON_VERSION = $CURRENT_PYTHON_VERSION"
pip3 --version
pip3 install --user pipenv
pipenv --version
sed -i -e 's/python_version = "3.8"/python_version = "'"$CURRENT_PYTHON_VERSION"'"/' Pipfile
PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
