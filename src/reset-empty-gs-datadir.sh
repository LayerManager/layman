#!/bin/bash

cd /code

mkdir -p tmp/geoserver/${GS_VERSION}/

gs_zip=tmp/geoserver/${GS_VERSION}/geoserver.zip
if ! [ -f $gs_zip ]; then
    rm -rf tmp/geoserver/${GS_VERSION}/*
    curl -L -o $gs_zip http://sourceforge.net/projects/geoserver/files/GeoServer/${GS_VERSION}/geoserver-${GS_VERSION}-war.zip
    unzip -q $gs_zip -d tmp/geoserver/${GS_VERSION}/
    mkdir -p tmp/geoserver/${GS_VERSION}/geoserver
    unzip -q tmp/geoserver/${GS_VERSION}/geoserver.war -d tmp/geoserver/${GS_VERSION}/geoserver
fi

mkdir -p /geoserver_data
rm -rf /geoserver_data/*
cp -r tmp/geoserver/${GS_VERSION}/geoserver/data/* /geoserver_data
rm -r /geoserver_data/coverages
rm -r /geoserver_data/data
rm -r /geoserver_data/layergroups
find /geoserver_data/styles/ -type f ! -name 'default*' -delete
rm -r /geoserver_data/styles/default_line2.sld
rm -r /geoserver_data/validation
rm -r /geoserver_data/workspaces
rm -r /geoserver_data/www
chmod -R a+rwx /geoserver_data
