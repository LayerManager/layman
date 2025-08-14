# Asynchronous tasks

Layman uses asynchronous tasks for processing publications (layers and maps), because some processing steps may take a long time. For example, importing 100 MB ShapeFile to DB may take few tens of seconds.

Asynchronous tasks are started by following requests:
- [POST Workspace Layers](rest.md#post-workspace-layers)
   - tasks related to newly published layer
   - tasks related to each map that points to newly published layer
- [PATCH Workspace Layer](rest.md#patch-workspace-layer)
   - tasks related to patched layer
   - tasks related to each map that points to patched layer
- [POST Workspace Maps](rest.md#post-workspace-maps)
   - tasks related to newly published map
- [PATCH Map](rest.md#patch-map)
   - tasks related to patched map
- [WFS-T](endpoints.md#web-feature-service)
   - tasks related to each edited vector layer
   - tasks related to each map that points to at least one edited vector layer

Each request starts series of asynchronous tasks called **chain**.
