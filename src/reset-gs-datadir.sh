#!/bin/bash

cd /code
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
