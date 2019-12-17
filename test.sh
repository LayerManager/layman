#!/bin/bash

bash src/clear-python-cache.sh

mkdir -p tmp/naturalearth/110m/cultural
mkdir -p tmp/naturalearth/10m/cultural

ne_110m_cultural=tmp/naturalearth/110m_cultural.zip
if ! [ -f $ne_110m_cultural ]; then
  curl -L -o $ne_110m_cultural "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/110m_cultural.zip"
  unzip -q $ne_110m_cultural -d tmp/naturalearth/110m/cultural
fi

ne_110m_cultural_admin_0_countries=tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson
if ! [ -f $ne_110m_cultural_admin_0_countries ]; then
  curl -L -o $ne_110m_cultural_admin_0_countries "https://github.com/nvkelso/natural-earth-vector/raw/master/geojson/ne_110m_admin_0_countries.geojson"
fi

ne_10m_cultural_admin_0_countries=tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson
if ! [ -f $ne_10m_cultural_admin_0_countries ]; then
  curl -L -o $ne_10m_cultural_admin_0_countries "https://github.com/nvkelso/natural-earth-vector/raw/master/geojson/ne_10m_admin_0_countries.geojson"
fi

ne_110m_cultural_populated_places=tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson
if ! [ -f $ne_110m_cultural_populated_places ]; then
  curl -L -o $ne_110m_cultural_populated_places "https://github.com/nvkelso/natural-earth-vector/raw/master/geojson/ne_110m_populated_places.geojson"
fi

mkdir -p tmp/artifacts
rm -rf tmp/artifacts/*

#python3 src/clear_layman_data.py && python3 -m pytest -svv src/layman/layer/rest_test.py::test_get_layers_testuser1_v1
python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xvv
#python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/common/metadata/util_test.py
#python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/layer/client_test.py
#python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/layer/rest_test.py::test_post_layers_complex src/layman/layer/rest_test.py::test_patch_layer_data src/layman/layer/rest_test.py::test_patch_layer_concurrent_and_delete_it


