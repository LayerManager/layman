# Endpoints
To use [headers for GeoServer's Proxy URL](https://docs.geoserver.org/2.21.x/en/user/configuration/globalsettings.html#use-headers-for-proxy-url) see [client proxy documentation](client-proxy.md).

## Web Map Service
[Web Map Service (WMS)](https://www.ogc.org/publications/standard/wms/) endpoint is implemented using combination of Layman's authentication proxy, Layman's WMS proxy, and [GeoServer](https://docs.geoserver.org/2.21.x/en/user/services/wms/reference.html).

The authentication proxy understands same [authentication credentials](security.md#authentication) as Layman REST API (e.g. OAuth2 credentials) and passes the request to GeoServer with credentials understandable by GeoServer.

The WMS proxy parses request and adapts it in case of WMS GetMap requests:
- If incoming request is in CRS:84 and  one of requested SLD layers has native CRS EPSG:5514, it changes CRS of the request to EPSG:4326. It fixes wrong transformation of features in GeoServer.

WMS respects [publication access rights](security.md#publication-access-rights). If user asks for layer he has not read access to by GetMap or GetFeatureInfo request, GeoServer returns standard ServiceExceptionReport (code LayerNotDefined).

### GetLegendGraphic
GetLegendGraphic query is answered directly by GeoServer for layers with SLD style and can be parametrized according to [GeoServer documentation](https://docs.geoserver.org/latest/en/user/services/wms/get_legend_graphic/index.html). For layers with QML style is such query redirected by GeoServer to QGIS server and can be parametrized according to [QGIS documentation](https://docs.qgis.org/3.16/en/docs/server_manual/services.html?highlight=getlegendgraphic#getlegendgraphics). 

## Web Feature Service
[Web Feature Service (WFS)](https://www.ogc.org/publications/standard/wfs/) endpoint is implemented using combination of Layman's authentication proxy, Layman's WFS proxy, and [GeoServer](https://docs.geoserver.org/2.21.x/en/user/services/wfs/reference.html).

The authentication proxy behaves in the same way as in case of [WMS](#web-map-service).

The WFS proxy parses request and adapts it in few ways in case of WFS-T 1.0, 1.1 and 2.0:
- If incoming WFS-T request Insert, Replace, or Update refers to an attribute, that does not exist yet in DB, the attribute is automatically created in DB table before redirecting WFS-T request to GeoServer. The attributes name must match to regex `^[a-zA-Z_][a-zA-Z_0-9]*$`, otherwise Layman error is raised. Data type of the attributes is `VARCHAR(1024)`. Also if QML style is used, attribute is automatically added to QGS project file. If attribute creation fails for any reason, warning is logged and request is forwarded to GeoServer nevertheless.
- Bounding box and thumbnail of each vector layer referenced in incoming Insert, Replace, Update, or Delete WFS-T request is updated in [asynchronous chain](async-tasks.md) after the request is finished.
- Calling WFS-T on a vector layer when previous asynchronous chain of the layer (POST, PATCH or another WFS-T) is still running causes run of WFS-T asynchronous chain after the current one is finished.
- Calling WFS-T on a vector layer that is contained by map whose previous asynchronous chain (POST, PATCH or another chain caused by WFS-T) is still running causes run of map's asynchronous chain after the current one is finished.

WFS respects [publication access rights](security.md#publication-access-rights). If user asks for type (layer) he has not read access to by DescribeFeatureType or GetFeature request, GeoServer returns standard ExceptionReport (code InvalidParameterValue, locator typeName or typeNames). To perform WFS-T requests, write access is needed.

### Known issues
For layers in `EPSG:5514` and WFS requests in `CRS:84`, the features may have wrong coordinates by hundreds of meters. For requests in `EPSG:4326`, coordinates are correct.

For layers with QML style, there is precision error about 3.2 meters in some WMS GetMap requests. The error appears if either data CRS or WMS GetMap CRS is `EPSG:5514` and the other one is not.

## Catalogue Service
[Catalogue Service (CSW)](https://www.ogc.org/publications/standard/cat/) is implemented using [Micka](https://github.com/hsrs-cz/Micka).
