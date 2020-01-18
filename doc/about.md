# About Layman

## Overview
Layman is a web service for publishing geospatial data online through REST API. It accepts vector data in GeoJSON or ShapeFile format together with visual styling and makes it accessible through standardized OGC APIs: Web Map Service, Web Feature Service, and Catalogue Service. Even large data files can be easily published thanks to chunk upload and asynchronous processing.

## Most Important Features

### Layers and Maps
Layman supports two main models of geospatial data: layers and maps. **Layer** is created from combination of vector data (GeoJSON or ShapeFile) and visualization (SLD or SE style). **Map** is collection of layers described in JSON format.

### Acessibility
There are multiple client applications for communication with Layman through its REST API: simple web test client shipped with Layman, QGIS desktop client, and HSLayers library. Published data are accessible through standardized OGC APIs: Web Map Service, Web Feature Service, and Catalogue Service.

### Security
Layman`s security system uses two well-known concepts: authentication and authorization. Common configuration consists of authentication based on widely used OAuth2 protocol and authorization ensuring that only owner of the data may edit it.

### Scalability
Large data files can be easily published thanks to chunk upload. Asynchronous processing ensures fast communication with REST API. Processing tasks can be distributed on multiple servers. Layman also stands on the shoulders of widely used programs like Flask, PostgreSQL, PostGIS, GDAL, GeoServer, Celery, and Redis.
