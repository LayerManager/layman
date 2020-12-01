# Endpoints

## Web Map Service
[Web Map Service (WMS)](https://www.opengeospatial.org/standards/wms) endpoint is implemented using combination of Layman's authentication proxy and [GeoServer](https://docs.geoserver.org/2.13.0/user/services/wms/reference.html).

The authentication proxy understands same [authentication credentials](security.md#authentication) as Layman REST API (e.g. OAuth2 credentials) and passes the request to GeoServer with credentials understandable by GeoServer.

WMS respects [publication access rights](security.md#publication-access-rights). If user asks for layer he has not read access to by GetMap or GetFeatureInfo request, GeoServer returns standard ServiceExceptionReport (code LayerNotDefined).

## Web Feature Service
[Web Feature Service (WFS)](https://www.opengeospatial.org/standards/wfs) endpoint is implemented using combination of Layman's authentication proxy, Layman's WFS proxy, and [GeoServer](https://docs.geoserver.org/2.13.0/user/services/wfs/reference.html).

The authentication proxy behaves in the same way as in case of [WMS](#web-map-service).

The WFS proxy automatically creates missing attributes in DB table before redirecting WFS-T request to GeoServer. Each missing attribute is created as `VARCHAR(1024)`. Works for WFS-T 1.0, 1.1 and 2.0 on actions Insert, Update and Replace. If creating attribute fails for any reason, warning is logged and request is forwarded to GeoServer nevertheless.

WFS respects [publication access rights](security.md#publication-access-rights). If user asks for type (layer) he has not read access to by DescribeFeatureType or GetFeature request, GeoServer returns standard ExceptionReport (code InvalidParameterValue, locator typeName or typeNames). To perform WFS-T requests, write access is needed.

## Catalogue Service
[Catalogue Service (CSW)](https://www.opengeospatial.org/standards/cat) is implemented using [Micka](https://github.com/hsrs-cz/Micka).
