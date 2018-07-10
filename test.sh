#!/bin/bash

ne_110m_cultural=tmp/naturalearth/110m_cultural.zip
mkdir -p tmp/naturalearth/110m/cultural
if ! [ -f $ne_110m_cultural ]; then
  curl -L -o $ne_110m_cultural "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/110m_cultural.zip"
  unzip -q $ne_110m_cultural -d tmp/naturalearth/110m/cultural
fi
python3 src/layman/prepare.py && pytest -svv
