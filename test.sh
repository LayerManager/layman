#!/bin/bash

bash src/clear-python-cache.sh

mkdir -p tmp/naturalearth/110m/cultural
mkdir -p tmp/naturalearth/50m/cultural
mkdir -p tmp/naturalearth/10m/cultural
mkdir -p tmp/data200/trans/jtsk
mkdir -p tmp/sm5/vektor/jtsk

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

ne_50m_cultural_admin_0_countries=tmp/naturalearth/50m/cultural/ne_50m_admin_0_countries.geojson
if ! [ -f $ne_50m_cultural_admin_0_countries ]; then
  curl -L -o $ne_50m_cultural_admin_0_countries "https://github.com/nvkelso/natural-earth-vector/raw/master/geojson/ne_50m_admin_0_countries.geojson"
fi

ne_110m_cultural_populated_places=tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson
if ! [ -f $ne_110m_cultural_populated_places ]; then
  curl -L -o $ne_110m_cultural_populated_places "https://github.com/nvkelso/natural-earth-vector/raw/master/geojson/ne_110m_populated_places.geojson"
fi

data200trans=tmp/data200/trans/trans-jtsk.zip
data200transJtsk=tmp/data200/trans/jtsk
data200transRoad=tmp/data200/trans/RoadL.shp
if ! [ -f $data200transRoad ]; then
  curl -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36" -L -o $data200trans "https://geoportal.cuzk.cz/ZAKAZKY/Data200/TRANS.zip"
  unzip -q $data200trans -d $data200transJtsk
  for f in tmp/data200/trans/jtsk/RoadL.shp
  do
   echo "Processing $f"
    ogr2ogr -t_srs EPSG:3857 -lco ENCODING=UTF-8 tmp/data200/trans/$(basename $f) $f
  done
fi

sm5building=tmp/sm5/vektor/sm5.zip
sm5VectorJtsk=tmp/sm5/vektor/jtsk
sm5VectorBuilding=tmp/sm5/vektor/Budova.shp
if ! [ -f $sm5VectorBuilding ]; then
  curl -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36" -L -o $sm5building "https://geoportal.cuzk.cz/UKAZKOVA_DATA/SM5_VEKTOR_NOVA.zip"
  unzip -q $sm5building -d $sm5VectorJtsk
  for f in tmp/sm5/vektor/jtsk/SM5_VEKTOR_NOVA/shp/Budova.shp
  do
   echo "Processing $f"
    ogr2ogr -s_srs EPSG:5514 -t_srs EPSG:3857 -lco ENCODING=UTF-8 tmp/sm5/vektor/$(basename $f) $f
  done
fi

mkdir -p tmp/artifacts
rm -rf tmp/artifacts/*

python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xvv
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning --capture=tee-sys -xvv src/layman/authz_change_test.py
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/layer/client_test.py
#python3 src/assert_db.py && python3 src/wait_for_deps.py && python3 src/clear_layman_data.py && python3 -m pytest -W ignore::DeprecationWarning -xsvv src/layman/layer/rest_test.py::test_post_layers_complex src/layman/layer/rest_test.py::test_patch_layer_data src/layman/layer/rest_test.py::test_patch_layer_concurrent_and_delete_it


