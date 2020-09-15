# Endpoints

## Web Map Service
[Web Map Service (WMS)](https://www.opengeospatial.org/standards/wms) endpoint is implemented using [GeoServer](https://docs.geoserver.org/2.13.0/user/services/wms/reference.html). No additional functionality is added by Layman.


## Web Feature Service
[Web Map Service (WMS)](https://www.opengeospatial.org/standards/wms) endpoint is implemented using combination of Layman's proxy and [GeoServer](https://docs.geoserver.org/2.13.0/user/services/wfs/reference.html).

Layman's proxy has two functions:
  - Understands same [authentication credentials](security.md#authentication) as Layman REST API (e.g. OAuth2 credentials) and passes authenticated user to GeoServer
  - Creates missing attributes in DB before redirecting WFS-T request to GeoServer. Each missing attribute is created as `VARCHAR(1024)`. Works for WFS-T 1.0, 1.1 and 2.0, actions Insert, Update and Replace. If creating attribute fails for any reason, warning is logged and request is redirected nevertheless.

## Catalogue Service
[Catalogue Service (CSW)](https://www.opengeospatial.org/standards/cat) is implemented using [Micka](https://github.com/hsrs-cz/Micka).
