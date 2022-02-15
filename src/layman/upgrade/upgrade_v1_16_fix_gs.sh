#!/bin/bash
set -ex

rm -rf tmp/security_backup
mv deps/geoserver/data/security tmp/security_backup
cp -r deps/geoserver/sample/geoserver_data/security deps/geoserver/data/
cp tmp/security_backup/layers.properties deps/geoserver/data/security/
sed -i 's/<entry key="passwd">.*<\/entry>/<entry key="passwd">crypt1:m5gQ0eitcA0++aYlVtK6CA==<\/entry>/g' deps/geoserver/data/workspaces/*/postgresql/datastore.xml

echo "*******************************************"
echo "GeoServer's Security successfully restored!"
echo "*******************************************"
