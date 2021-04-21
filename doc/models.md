# Models

## Publication
- Publication is any geospatial data that can be published by Layman through [REST API](rest.md).
- Currently available publications are [map](#map) and [layer](#layer). 
- Each publication is placed in one [workspace](#workspace). 

## Layer
- Layer is [publication](#publication) created from combination of vector data (GeoJSON or ShapeFile) and visualization (SLD or SE style)
- Published layer can be accessed by standardized OGC interfaces
  - [Web Map Service (WMS)](https://www.opengeospatial.org/standards/wms)
  - [Web Feature Service (WFS)](https://www.opengeospatial.org/standards/wfs)
  - [Catalogue Service](https://www.opengeospatial.org/standards/cat)
- Thumbnail image available
- Layer-related data is named and structured 
  - either by [workspace](#workspace) name and layername
      - [REST API](rest.md): `/rest/workspaces/<workspace_name>/layers/<layername>` 
      - [filesystem](data-storage.md#filesystem): `/path/to/LAYMAN_DATA_DIR/workspaces/<workspace_name>/layers/<layername>` 
      - [PostgreSQL](data-storage.md#postgresql): `db=LAYMAN_PG_DBNAME, schema=<workspace_name>, table=<layername>` 
      - [GeoServer WFS](data-storage.md#geoserver): `/geoserver/<workspace_name>/ows, layer=<layername>`
      - [GeoServer WMS](data-storage.md#geoserver): `/geoserver/<workspace_name>_wms/ows, layer=<layername>, style=<layername>`
  - or by UUID:
      - Micka: `/record/basic/m-<uuid>`
- Simple rules
  - one DB table per input file
  - one WFS feature type per DB table
  - one WMS layer per DB table
  - one SLD or QGIS style per WMS layer
  - one thumbnail per WMS layer
  - one metadata record per WMS&WFS layer
  
## Map
- Also referred to as **map composition**
- Map is [publication](#publication) defined by JSON valid against [map-composition schema](https://github.com/hslayers/hslayers-ng/wiki/Composition-schema) ([source](https://github.com/hslayers/hslayers-ng/blob/develop/projects/hslayers/src/components/compositions/schema.json)) used by [Hslayers-ng](https://github.com/hslayers/hslayers-ng)
- Map is collection of WMS layers and vector data
- Maps composed from WMS layers only are fully supported
- Documented [map publishing](publish-map.md) process 
- Thumbnail image available
- Map-related data is named and structured
  - either by [workspace](#workspace) and layername
      - [REST API](rest.md): `/rest/workspaces/<workspace_name>/maps/<mapname>` 
      - file system: `/path/to/LAYMAN_DATA_DIR/workspaces/<workspace_name>/maps/<mapname>` 
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
- Username is a string identifying one [user](#user), so it is unique among all users.
- The string is lower-case (in contrast with [role name](#role)).
- Each user is represented by max. one username.
- Username is also used to identify user's [personal workspace](#personal-workspace) when communicating with [Layman REST API](rest.md).
- Username can be reserved by [PATCH Current User](rest.md#patch-current-user).
- Anonymous user has no username.

## Role
- Role is any group of users. One user can be assigned to multiple roles.
- Each role is identified by name that is unique among all roles.
- The name is upper-case (in contrast with [username](#username)).
- Roles can be used for assigning access rights.

## Workspace
- Workspace is folder for [publications](#publication).
- Each workspace is identified by name that is unique among all workspaces.
- Workspace name is sometimes used for structuring publication-related data. For example, it's part of REST API URL (`/rest/workspaces/<workspace_name>/...`), directory names (`<LAYMAN_DATA_DIR>/workspaces/<workspace_name>/...`), DB schemas, or OGC Web Services (`/geoserver/<workspace_name>/...`, `/geoserver/<workspace_name>_wms/...`).
- Workspace's REST API consists of all [map and layer endpoints](rest.md) endpoints.
- There are following types of workspaces:
   - [Personal workspace](#personal-workspace)
   - [Public workspace](#public-workspace)

## Personal workspace
- Personal workspace is a [workspace](#workspace) whose name is equal to [username](#username) of some [user](#user).
- Such user is considered as **owner** of this workspace and he is the only one who can publish new publications in this workspace.
- Personal workspace is created automatically when [username](#username) is reserved.

## Public workspace
- Public workspace is a [workspace](#workspace) whose name is not equal to any [username](#username).
- Public workspace has no **owner**.
- Only users listed in [GRANT_PUBLISH_IN_PUBLIC_WORKSPACE](env-settings.md#GRANT_PUBLISH_IN_PUBLIC_WORKSPACE) can publish new publications in public workspace.
- Public workspace is automatically created when first [publication](#publication) is being published there. Only users listed in [GRANT_CREATE_PUBLIC_WORKSPACE](env-settings.md#GRANT_CREATE_PUBLIC_WORKSPACE) can create new public workspace in this way.
