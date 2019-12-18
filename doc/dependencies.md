
## Main dependencies

| name | version | license | used by | env | bin or src | purpose |
| --- | --- | --- | --- | --- | --- | --- |
| [python](http://www.gdal.org/) | 3.5 | Python Software Foundation License | geographicags/docker-gdal2 | prod | bin | to communicate |
| [flask](http://flask.pocoo.org/) | 1.0.2 | BSD License | Pipfile | prod | bin | to build REST API |
| [gdal](http://www.gdal.org/) | 2.3.0 | MIT License | geographicags/docker-gdal2 | prod | bin | to import vector files into DB |
| [postgresql](https://www.postgresql.org/) | 10.0 | PostgreSQL | kartoza/docker-postgis | prod-external | bin | to store vector data effectively |
| [postgis](https://postgis.net/) | 2.4 | GNU GPL v2 | kartoza/docker-postgis | prod-external | bin | to store vector data effectively |
| [geoserver](https://github.com/geoserver/geoserver) | 2.13.0 | GNU GPL v2 | kartoza/docker-geoserver | prod-external | bin | to provide WMS/WFS endpoints |
| [redis](https://redis.io/) | 4.0.11 | BSD 3-Clause | docker-library/redis | prod-external | bin | celery message broker, source of truth for server side |
| [celery](http://www.celeryproject.org/) | 4.2.1 | BSD 3-Clause | Pipfile | prod | bin | asynchronous task runner |
| [layman-test-client](https://github.com/jirik/layman-test-client) | 1.0.0 | GNU GPL v3 | docker-compose.*.yml | opt | bin | to demonstrate communication with REST API |
| [liferay portal](https://portal.liferay.dev/) | 7.1.3 | GNU GPL v2 | liferay/portal | opt | bin | as OAuth2 provider |
| [micka](https://github.com/hsrs-cz/Micka) | [e6f083b](https://github.com/hsrs-cz/Micka/tree/e6f083bb2cf6a54a1893e97b7525d3369fa64b1e) | BSD 3-Clause | jirikcz/micka | prod-external | bin | to provide CSW endpoint |

## Other dependencies

| name | license | used by | env | bin or src | purpose |
| --- | --- | --- | --- | --- | --- |
| [gunicorn](https://gunicorn.org/) | MIT | requirements.production.txt | opt | bin | as Flask production server |
| [nginx](http://nginx.org/) | BSD 2-Clause | docker-compose.*demo.yml | opt | bin | as production server |
| [openlayers](https://openlayers.org/) | BSD 2-Clause | package.json | prod | bin | for client-side map rendering |
| [hslayers-ng](https://github.com/hslayers/hslayers-ng) | MIT | schema.draft-07.json | prod | src | |
| [jsonschema](https://github.com/Julian/jsonschema) | MIT | Pipfile | prod | bin | |
| [redis-py](https://github.com/andymccurdy/redis-py) | MIT | Pipfile | prod | bin | |
| [owslib](https://github.com/geopython/OWSLib) | BSD 3-Clause | Pipfile | prod | bin | |
| [cacheout](https://github.com/dgilland/cacheout) | MIT | Pipfile | prod | bin | |
| [requests](http://python-requests.org) | Apache License 2.0 | Pipfile | prod | bin | |
| [psycopg2-binary](https://github.com/psycopg/psycopg2) | GNU LGPL | Pipfile | prod | bin | |
| [unidecode](https://github.com/avian2/unidecode) | GNU GPL v2 | Pipfile | prod | bin | |
| [selenium](https://www.chromium.org/) | Apache License 2.0 | Dockerfile.dev | prod | bin | for client-side map rendering and integration testing |
| [chromium](https://www.chromium.org/) | BSD and others | Dockerfile.dev | prod | bin | for client-side map rendering and integration testing |
| [chromedriver](http://chromedriver.chromium.org/) | BSD and others | Dockerfile.dev | prod | bin | for client-side map rendering and integration testing |
| [flower](https://github.com/mher/flower) | BSD 3-Clause | Pipfile | dev | bin | to monitor celery tasks |
| [watchdog](https://github.com/gorakhargosh/watchdog) | Apache License 2.0 | Pipfile | dev | bin | |
| [pytest](https://pytest.org/) | MIT License | Pipfile | test | bin | |
| [geographicags/docker-gdal2](https://github.com/GeographicaGS/Docker-GDAL2) | MIT License | Dockerfile | prod | bin | |
| [kartoza/docker-geoserver](https://github.com/kartoza/docker-geoserver) | GNU GPL v2 | docker-compose.dev.yml | dev | bin | |
| [kartoza/docker-postgis](https://github.com/kartoza/docker-postgis) | - | docker-compose.dev.yml | dev | bin | |
| [docker-library/tomcat](https://github.com/docker-library/tomcat) | Apache License 2.0 | kartoza/docker-geoserver | dev | bin | |
| [apache/tomcat](http://tomcat.apache.org/) | Apache License 2.0 | docker-library/tomcat | dev | bin | |
| [docker-library/openjdk](https://github.com/docker-library/openjdk) | MIT License | docker-library/tomcat | dev | bin | |
| [java/openjdk](http://openjdk.java.net/) | GNU GPL v2 | docker-library/openjdk | dev | bin | |
| [docker-library/buildpack-deps](https://github.com/docker-library/buildpack-deps) | MIT License | docker-library/openjdk | dev | bin | |
| [debuerreotype/docker-debian-artifacts](https://github.com/debuerreotype/docker-debian-artifacts) | Apache License 2.0 | docker-library/buildpack-deps, kartoza/docker-postgis | dev | bin | |
| [debian](https://www.debian.org/) | GNU GPL mostly | debuerreotype/docker-debian-artifacts | dev | bin | |
| [liferay/portal](https://github.com/docker-library/redis) | GNU GPL v2 | docker-compose.*.yml | opt | bin | |
| [jirikcz/micka](https://github.com/jirik/docker-micka) | GNU GPL v3 | docker-compose.*.yml | prod-external | bin | |
| [samtux/micka](https://github.com/samtux/docker-micka) | GNU GPL v3 | jirikcz/micka | prod-external | src | |
| [docker-library/redis](https://github.com/docker-library/redis) | BSD 3-Clause | docker-compose.*.yml | prod | bin | |
| [gliderlabs/docker-alpine](https://github.com/gliderlabs/docker-alpine) | BSD 3-Clause | docker-library/redis | prod | bin | |
| [alpine-linux](https://alpinelinux.org/) | GNU GPL mostly | gliderlabs/docker-alpine | prod | bin | |
