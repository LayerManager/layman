# O Laymanovi

## Úvod
Layman je služba pro publikování geoporostorových dat na webu prostřednictvím REST API. Layman přijímá vektorová i rastrová data například ve formátech GeoJSON, ShapeFile GeoTIFF nebo JPEG2000 a spolu s vizuálním stylem je zpřístupňuje přes standardizovaná OGC rozhraní: Web Map Service, Web Feature Service a Catalogue Service. Layman umožňuje snadno publikovat i velké soubory dat, a to díky uploadu po částech a asynchronnímu zpracování.

## Nejdůležitější vlastnosti

### Vrstvy a mapy
Layman podporuje dva základní modely geoprostorových dat: vrstvy a mapy. **Vrstva** je tvořena kombinací vektorových nebo rastrových dat (GeoJSON, ShapeFile, GeoTIFF, JPEG2000, PNG nebo JPEG) a vizualizace (SLD, SE nebo QML styl). Rastrová vrstva může mít podobu i časové série několika snímků. **Mapa** je kolekcí vrstev, která je popsána ve formátu JSON.


### Přístupnost
Existuje více klientských aplikací pro komunikaci s Laymanem prostřednictvím jeho REST API: jednoduchý testovací webový klient, desktopový klient v QGISu a knihovna HSLayers. Publikovaná data jsou přístupná přes standardizovaná OGC rozhraní: Web Map Service, Web Feature Service a Catalogue Service.

### Bezpečnost
Bezpečnostní systém Laymana využívá dvou známých konceptů: autentizace a autorizace. Běžná konfigurace sestává z autentizace založené na protokolu OAuth2 a autorizace zajišťující, že pouze vlastník dat má práva na jejich editaci.

### Škálovatelnost
Díky uploadu po částech lze snadno publikovat i velké soubory dat. Asynchronní zpracování zajišťuje rychlou komunikaci s REST API. Zpracování dat může být distribuováno na více serverů. Layman stojí na ramenou široce využívaných programů, mezi než patří Flask, PostgreSQL, PostGIS, GDAL, GeoServer, QGIS Server, Celery a Redis.
