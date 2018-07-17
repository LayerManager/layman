#!/bin/bash

cd /code
mkdir -p tmp/geoserver/${GS_VERSION}/
rm -rf tmp/geoserver/${GS_VERSION}/*
curl -L -o tmp/geoserver/${GS_VERSION}/geoserver.zip http://sourceforge.net/projects/geoserver/files/GeoServer/${GS_VERSION}/geoserver-${GS_VERSION}-war.zip
unzip -q tmp/geoserver/${GS_VERSION}/geoserver.zip -d tmp/geoserver/${GS_VERSION}/
mkdir -p tmp/geoserver/${GS_VERSION}/geoserver
unzip -q tmp/geoserver/${GS_VERSION}/geoserver.war -d tmp/geoserver/${GS_VERSION}/geoserver
