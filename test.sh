#!/bin/bash

bash src/clear-python-cache.sh

bash src/ensure-test-client.sh

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

#python3 src/clear_layman_data.py && python3 src/prepare_layman.py && pytest -svv
python3 src/clear_layman_data.py && python3 src/prepare_layman.py && pytest -svv -k "not resumable_test" && pytest -svv -k "resumable_test"
#python3 src/clear_layman_data.py && python3 src/prepare_layman.py && pytest -svv -k "resumable_test"
