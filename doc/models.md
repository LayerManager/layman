# Models

## Publication
- Publication is any geospatial data that can be published by Layman through [REST API](rest.md).
- Available publications are [map](#map) and [layer](#layer). 
- Each publication is placed in one [workspace](#workspace). 

## Layer
- Layer is [publication](#publication) created from combination of vector or raster data (GeoJSON, ShapeFile, PostGIS table, GeoTIFF, JPEG2000, PNG or JPEG) and visualization (SLD, SE, or QML style). Raster layer can hold also [timeseries](#timeseries) data.
- Published layer can be accessed by standardized OGC interfaces
  - [Web Map Service (WMS)](https://www.ogc.org/standards/wms/)
  - [Web Feature Service (WFS)](https://www.ogc.org/standards/wfs/)
  - [Catalogue Service](https://www.ogc.org/standards/cat/)
- Thumbnail image available
- Layer-related data is named and structured 
  - either by [workspace](#workspace) name and layername
      - [REST API](rest.md): `/rest/workspaces/<workspace_name>/layers/<layername>` 
  - or by UUID:
      - [filesystem](data-storage.md#filesystem): `/path/to/LAYMAN_DATA_DIR/layers/<UUID>` 
      - [PostgreSQL](data-storage.md#postgresql): `db=LAYMAN_PG_DBNAME, schema=layers, table=layer_<UUID>` 
      - [GeoServer WFS](data-storage.md#geoserver): `/geoserver/layman/ows, layer=l_<UUID>`
      - [GeoServer WMS](data-storage.md#geoserver): `/geoserver/layman_wms/ows, layer=l_<UUID>, style=<UUID>`
      - Micka: `/record/basic/m-<UUID>`
      - [REST API](rest.md): `/rest/layers/<uuid>/thumbnail`
- Simple rules
  - one DB table per input file (vector layers only)
  - one WFS feature type per DB table (vector layers only)
    - exception: external PostGIS table can be published as multiple WFS feature types
  - one WMS layer per DB table
    - exception: external PostGIS table can be published as multiple WMS layers
  - one SLD or QGIS style per WMS layer
  - one thumbnail per WMS layer
  - one metadata record per WMS&WFS layer

## Timeseries
- Timeseries is [layer](#layer) created from set of raster data files (GeoTIFF, JPEG2000, PNG or JPEG).
- Each file represents one time instant, more files may represent the same time instant.
- The smallest possible supported temporal unit is one day (see [#875](https://github.com/LayerManager/layman/issues/875)).
- Information about time representation is passed through [time_regex](rest.md#post-workspace-layers) parameter.
  
## Map
- Also referred to as **map composition**
- Map is [publication](#publication) defined by JSON valid against [map-composition schema](https://github.com/hslayers/map-compositions) version 2 or 3 used by [Hslayers-ng](https://github.com/hslayers/hslayers-ng)
- Map is collection of WMS layers and vector data
- Maps composed of WMS layers only are fully supported
- Each layer is either [internal](#internal-map-layer), or [external](#external-map-layer).
- Documented [map publishing](publish-map.md) process 
- Thumbnail image available
- Map-related data is named and structured
  - either by [workspace](#workspace) and layername
      - [REST API](rest.md): `/rest/workspaces/<workspace_name>/maps/<mapname>` 
  - or by UUID:
      - [filesystem](data-storage.md#filesystem): `/path/to/LAYMAN_DATA_DIR/maps/<UUID>` 
      - [REST API](rest.md): `/rest/maps/<uuid>/thumbnail`
      - Micka: `/record/basic/m-<uuid>`
- Simple rules
  - one map file per map
  - one thumbnail per map
  - one metadata record per map

### Internal map layer
- Internal map layer is layer of the [map](#map) named `l_<UUID>` in `layman` or `layman_wms` workspace, and
    - whose `className` is `WMS` (or ends with `.WMS`) and whose `url` points to the Layman instance,
    - or whose `className` is `Vector` (or ends with `.Vector`), whose `protocol.format` is `WFS` (or ends with `.WFS`) and whose `protocol.url` points to the Layman instance.
- Map layer is considered internal even if [layer](#layer) with UUID does not currently exist in the Layman instance.

### External map layer
- External map layer is layer of the [map](#map) that is not [internal](#internal-map-layer).

## User
- User is any person who communicates with Layman REST API through any client.
- User can be either authenticated, or unauthenticated (i.e. anonymous).
- User is sometimes identified by [username](#username)
- List of users with usernames can be obtained by [GET Users](rest.md#get-users).

## Username
- Username is a string identifying one [user](#user), so it is unique among all users.
- The string is lower-case (in contrast with [role name](#role)), maximum length is 59 characters.
- Each user is represented by max. one username.
- Username is also used to identify user's [personal workspace](#personal-workspace) when communicating with [Layman REST API](rest.md).
- Username can be reserved by [PATCH Current User](rest.md#patch-current-user).
- Usernames can be used for assigning access rights.
- Anonymous user has no username.

## Role
- Role is any group of users. One user can be assigned to multiple roles.
- Each role is identified by name that is unique among all roles.
- The name is upper-case (in contrast with [username](#username)), maximum length is 64 characters.
- Role names can be used for assigning access rights.
- Existing roles can be obtained by [GET Roles](rest.md#get-roles).
  - There is always listed special pseudo-role `EVERYONE` that represents every user including anonymous (unauthenticated).
- Roles (except of `EVERYONE`) are managed by [role service](security.md#role-service).

## Workspace
- Workspace is folder for [publications](#publication).
- Each workspace is identified by name that is unique among all workspaces.
- The name is lower-case, maximum length is 59 characters.
- Workspace name is sometimes used for structuring publication-related data. For example, it's part of REST API URL (`/rest/workspaces/<workspace_name>/...`).
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
