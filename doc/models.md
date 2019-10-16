# Models

## Publication
- Publication is any geospatial data that can be published by Layman. Currently available publications are [map](#map) and [layer](#layer). 

## Layer
- Layer is [publication](#publication) created from combination of vector data (GeoJSON or ShapeFile) and visualization (SLD or SE style)
- Even large files can be uploaded from browser
- Asynchronous upload and processing
- Provides URL endpoints:
  - WMS (powered by GeoServer)
  - WFS (powered by GeoServer)
  - thumbnail
- And other internal sources:
  - input files saved in file system
  - DB table with imported input file
- Layer-related data is named and structured first by user name, second by layer name
  - [REST API](doc/rest.md): `/rest/<username>/layers/<layername>` 
  - file system: `/path/to/LAYMAN_DATA_DIR/users/<username>/layers/<layername>` 
  - DB: `db=LAYMAN_PG_DBNAME, schema=<username>, table=<layername>` 
  - WMS/WFS: `/geoserver/<username>/ows, layer=<layername>, style=<layername>` 
- Simple rules
  - one DB table per input file
  - one WFS feature type per DB table
  - one WMS layer per DB table
  - one SLD style per WMS layer
  - one thumbnail per WMS layer
  
## Map
- Also referred to as **map composition**
- Map is [publication](#publication) defined by JSON valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema) ([source](https://github.com/hslayers/hslayers-ng/blob/develop/components/compositions/schema.json)) used by [Hslayers-ng](https://github.com/hslayers/hslayers-ng)
- Maps composed from WMS layers only are fully supported
- Asynchronous processing of map thumbnail
- Map-related data is named and structured first by user name, second by map name
  - [REST API](doc/rest.md): `/rest/<username>/maps/<mapname>` 
  - file system: `/path/to/LAYMAN_DATA_DIR/users/<username>/maps/<mapname>` 
  
