# Models

## Publication
- Publication is any geospatial data that can be published by Layman through [REST API](rest.md).
- Currently available publications are [map](#map) and [layer](#layer). 

## Layer
- Layer is [publication](#publication) created from combination of vector data (GeoJSON or ShapeFile) and visualization (SLD or SE style)
- Published layer can be accessed by standardized OGC interfaces
  - [Web Map Service (WMS)](https://www.opengeospatial.org/standards/wms)
  - [Web Feature Service (WFS)](https://www.opengeospatial.org/standards/wfs)
  - [Catalogue Service](https://www.opengeospatial.org/standards/cat)
- Thumbnail image available
- Layer-related data is named and structured 
  - either by username and layername
      - [REST API](rest.md): `/rest/<username>/layers/<layername>` 
      - [filesystem](data-storage.md#filesystem): `/path/to/LAYMAN_DATA_DIR/users/<username>/layers/<layername>` 
      - [PostgreSQL](data-storage.md#postgresql): `db=LAYMAN_PG_DBNAME, schema=<username>, table=<layername>` 
      - [GeoServer WMS/WFS](data-storage.md#geoserver): `/geoserver/<username>/ows, layer=<layername>, style=<layername>` 
  - or by UUID:
      - Micka: `/record/basic/m-<uuid>`
- Simple rules
  - one DB table per input file
  - one WFS feature type per DB table
  - one WMS layer per DB table
  - one SLD style per WMS layer
  - one thumbnail per WMS layer
  - one metadata record per WMS&WFS layer
  
## Map
- Also referred to as **map composition**
- Map is [publication](#publication) defined by JSON valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema) ([source](https://github.com/hslayers/hslayers-ng/blob/develop/components/compositions/schema.json)) used by [Hslayers-ng](https://github.com/hslayers/hslayers-ng)
- Map is collection of WMS layers and vector data
- Maps composed from WMS layers only are fully supported
- Documented [map publishing](publish-map.md) process 
- Thumbnail image available
- Map-related data is named and structured
  - either by username and layername
      - [REST API](rest.md): `/rest/<username>/maps/<mapname>` 
      - file system: `/path/to/LAYMAN_DATA_DIR/users/<username>/maps/<mapname>` 
  - or by UUID:
      - Micka: `/record/basic/m-<uuid>`
- Simple rules
  - one map file per map
  - one thumbnail per map
  - one metadata record per map

## User
- User is any person who communicates with Layman REST API through any client.
- User can be either authenticated, or unauthenticated (i.e. anonymous).
- User is sometimes identified by [username](#username)

## Username
- Username is a string identifying one [user](#user), so it is unique among all users
- Every user is represented by max. one username 
- Username is typically used to identify user's [workspace](#workspace) when communicating with [Layman REST API](rest.md)
- Username can re reserved by [PATCH Current User](rest.md#patch-current-user)
- Anonymous user has no username

## Role
- Role is any group of users. One user can be assigned to multiple roles.
- Each role is identified by name that is unique among all roles.
- The name is upper-case (in contrast with [username](#username)).
- Roles can be used for assigning access rights.

## Workspace
- Workspace is group of Layman REST API endpoints whose URL path starts with the same `username` (i. e. `/rest/<username>`)
- User represented by the `username` is considered as **owner** of the workspace
- Workspace consists of all [map and layer endpoints](rest.md) endpoints
