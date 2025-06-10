#!/bin/bash

set -ex

bash src/clear-python-cache.sh

mkdir -p tmp/naturalearth/110m/cultural
mkdir -p tmp/naturalearth/50m/cultural
mkdir -p tmp/naturalearth/10m/cultural
mkdir -p tmp/data200/trans/jtsk
mkdir -p tmp/sm5/vektor/jtsk

if ! [ -f tmp/naturalearth/110m/files.txt ]; then
  echo "https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_boundary_lines_land.cpg
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_boundary_lines_land.dbf
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_boundary_lines_land.prj
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_boundary_lines_land.README.html
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_boundary_lines_land.shp
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_boundary_lines_land.shx
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_countries.cpg
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_countries.dbf
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_countries.prj
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_countries.README.html
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_countries.shp
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_countries.shx
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_admin_0_countries.VERSION.txt
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_populated_places.cpg
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_populated_places.dbf
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_populated_places.prj
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_populated_places.README.html
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_populated_places.shp
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_populated_places.shx
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/110m_cultural/ne_110m_populated_places.VERSION.txt
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/geojson/ne_110m_admin_0_countries.geojson
https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/geojson/ne_110m_populated_places.geojson" > tmp/naturalearth/110m/files.txt

  (cd tmp/naturalearth/110m/cultural; xargs -n 1 curl -L -O < ../files.txt)
fi

ne_10m_cultural_admin_0_countries=tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson
if ! [ -f $ne_10m_cultural_admin_0_countries ]; then
  curl -L -o $ne_10m_cultural_admin_0_countries "https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/geojson/ne_10m_admin_0_countries.geojson"
fi

ne_50m_cultural_admin_0_countries=tmp/naturalearth/50m/cultural/ne_50m_admin_0_countries.geojson
if ! [ -f $ne_50m_cultural_admin_0_countries ]; then
  curl -L -o $ne_50m_cultural_admin_0_countries "https://github.com/nvkelso/natural-earth-vector/raw/v4.1.0/geojson/ne_50m_admin_0_countries.geojson"
fi

data200trans=tmp/data200/trans/trans-jtsk.zip
data200transJtsk=tmp/data200/trans/jtsk
data200transRoad=tmp/data200/trans/RoadL.shp
if ! [ -f $data200transRoad ]; then
  curl -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36" -L -o $data200trans "https://watlas.lesprojekt.cz/maps/layman/TRANS.zip"
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
