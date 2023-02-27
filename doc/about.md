# About Layman

## Overview
Layman is a web service for publishing geospatial data online through REST API. It accepts vector and raster data in GeoJSON, ShapeFile, PostGIS table, GeoTIFF, JPEG2000 and other formats together with visual styling and makes it accessible through standardized OGC APIs: Web Map Service, Web Feature Service, and Catalogue Service. Even large data files can be easily published thanks to chunk upload and asynchronous processing.

## Most Important Features

### Layers and Maps
Layman supports two main models of geospatial data: layers and maps. **Layer** is created from combination of vector or raster data (GeoJSON, ShapeFile, PostGIS table, GeoTIFF, JPEG2000, PNG, or JPEG) and visualization (SLD, SE or QML style). Raster layer can hold also timeseries data. **Map** is collection of layers described in JSON format.

### Acessibility
There are multiple client applications for communication with Layman through its REST API: simple web test client shipped with Layman, QGIS desktop client, and HSLayers library. Published data are accessible through standardized OGC APIs: Web Map Service, Web Feature Service, and Catalogue Service.

### Security
Layman`s security system uses two well-known concepts: authentication and authorization. Common configuration consists of authentication based on widely used OAuth2 protocol and authorization allows users to give read and write access rights to each user on publication level. 

### Scalability
Large data files can be easily published thanks to chunk upload. Asynchronous processing ensures fast communication with REST API. Processing tasks can be distributed on multiple servers. Layman also stands on the shoulders of widely used programs like Flask, PostgreSQL, PostGIS, GDAL, GeoServer, QGIS Server, Celery, and Redis.
