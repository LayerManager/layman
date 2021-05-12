# Endpoints

## Web Map Service
[Web Map Service (WMS)](https://www.opengeospatial.org/standards/wms) endpoint is implemented using combination of Layman's authentication proxy and [GeoServer](https://docs.geoserver.org/2.13.0/user/services/wms/reference.html).

The authentication proxy understands same [authentication credentials](security.md#authentication) as Layman REST API (e.g. OAuth2 credentials) and passes the request to GeoServer with credentials understandable by GeoServer.

WMS respects [publication access rights](security.md#publication-access-rights). If user asks for layer he has not read access to by GetMap or GetFeatureInfo request, GeoServer returns standard ServiceExceptionReport (code LayerNotDefined).

## Web Feature Service
[Web Feature Service (WFS)](https://www.opengeospatial.org/standards/wfs) endpoint is implemented using combination of Layman's authentication proxy, Layman's WFS proxy, and [GeoServer](https://docs.geoserver.org/2.13.0/user/services/wfs/reference.html).

The authentication proxy behaves in the same way as in case of [WMS](#web-map-service).

The WFS proxy parses request and adapts it in few ways in case of WFS-T 1.0, 1.1 and 2.0:
- If incoming WFS-T request Insert, Replace, or Update refers to an attribute, that does not exist yet in DB, the attribute is automatically created in DB table before redirecting WFS-T request to GeoServer. Data type of the attributes is `VARCHAR(1024)`. Also if QML style is used, attribute is automatically added to QGS project file. If attribute creation fails for any reason, warning is logged and request is forwarded to GeoServer nevertheless.
- Bounding box and thumbnail of each layer referenced in incoming Insert, Replace, Update, or Delete WFS-T request is updated in [asynchronous chain](async-tasks.md) after the request is finished.
- Calling WFS-T on a layer when previous asynchronous chain (POST, PATCH or another WFS-T) is still running causes run of WFS-T asynchronous chain after the current one is finished.

WFS respects [publication access rights](security.md#publication-access-rights). If user asks for type (layer) he has not read access to by DescribeFeatureType or GetFeature request, GeoServer returns standard ExceptionReport (code InvalidParameterValue, locator typeName or typeNames). To perform WFS-T requests, write access is needed.

## Catalogue Service
[Catalogue Service (CSW)](https://www.opengeospatial.org/standards/cat) is implemented using [Micka](https://github.com/hsrs-cz/Micka).
