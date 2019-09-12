#!/bin/bash

rm -rf ${GEOSERVER_DATA_DIR}/*
cp -r /geoserver_sample/geoserver_data/* ${GEOSERVER_DATA_DIR}/
