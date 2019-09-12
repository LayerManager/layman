#!/bin/bash

mkdir -p /geoserver_tmp/geoserver/${GS_VERSION}/

gs_zip=/geoserver_tmp/geoserver/${GS_VERSION}/geoserver.zip
if ! [ -f $gs_zip ]; then
    rm -rf /geoserver_tmp/geoserver/${GS_VERSION}/*
    curl -L -o $gs_zip http://sourceforge.net/projects/geoserver/files/GeoServer/${GS_VERSION}/geoserver-${GS_VERSION}-war.zip
    unzip -q $gs_zip -d /geoserver_tmp/geoserver/${GS_VERSION}/
    mkdir -p /geoserver_tmp/geoserver/${GS_VERSION}/geoserver
    unzip -q /geoserver_tmp/geoserver/${GS_VERSION}/geoserver.war -d /geoserver_tmp/geoserver/${GS_VERSION}/geoserver
fi

mkdir -p ${GEOSERVER_DATA_DIR}
rm -rf ${GEOSERVER_DATA_DIR}/*
cp -r /geoserver_tmp/geoserver/${GS_VERSION}/geoserver/data/* ${GEOSERVER_DATA_DIR}
rm -r ${GEOSERVER_DATA_DIR}/coverages
rm -r ${GEOSERVER_DATA_DIR}/data
rm -r ${GEOSERVER_DATA_DIR}/layergroups
find ${GEOSERVER_DATA_DIR}/styles/ -type f ! -name 'default*' -delete
rm -r ${GEOSERVER_DATA_DIR}/styles/default_line2.sld
rm -r ${GEOSERVER_DATA_DIR}/validation
rm -r ${GEOSERVER_DATA_DIR}/workspaces
rm -r ${GEOSERVER_DATA_DIR}/www
chmod -R a+rwx ${GEOSERVER_DATA_DIR}
