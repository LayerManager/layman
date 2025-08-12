
## External dependencies

| name | version | license | used by | env | bin or src | purpose |
| --- | --- | --- | --- | --- | --- | --- |
| [postgresql](https://www.postgresql.org/) | 13.3 | PostgreSQL | layermanager/docker-postgis | prod-external | bin | to store vector data effectively |
| [postgis](https://postgis.net/) | 3.1 | GNU GPL v2 | layermanager/docker-postgis | prod-external | bin | to store vector data effectively |
| [geoserver](https://github.com/geoserver/geoserver) | 2.26.2 | GNU GPL v2 | docker.osgeo.org/geoserver | prod-external | bin | to provide WMS/WFS endpoints |
| [qgis-server](https://docs.qgis.org/3.40/en/docs/server_manual/index.html) | 3.40.4 | GNU GPL v2 | layermanager/qgis-server | prod-external | bin | to provide WMS endpoint |
| [redis](https://redis.io/) | 4.0.11 | BSD 3-Clause | docker-library/redis | prod-external | bin | celery message broker, source of truth for server side |
| [micka](https://github.com/hsrs-cz/Micka) | [v2020.014](https://github.com/hsrs-cz/Micka/releases/tag/v2020.014) | BSD 3-Clause | jirikcz/micka | prod-external | bin | to provide CSW endpoint |
| [Wagtail](https://wagtail.org/) + [extensions](#wagtail-extensions) | 4.2 | BSD 3-Clause | deps/wagtail/laymanportal/requirements.txt | opt | bin | as OAuth2 provider |


## Internal dependencies

### System dependencies

| name | version | license | used by | env | bin or src | purpose |
| --- | --- | --- | --- | --- | --- | --- |
| [python](https://www.python.org/) | 3.8 | Python Software Foundation License | gdal/docker | prod | bin | to run Layman |
| [python3-lxml](https://lxml.de/installation.html) | 5.3 | BSD 3-Clause | Dockerfile | prod | bin | to query XML with full XPath 1.0 |
| [gdal](http://www.gdal.org/) | 3.3.0 | MIT | gdal/docker | prod | bin | to import vector files into DB |
| [firefox](https://www.mozilla.org/firefox/) | 95+ | MPL | Dockerfile | prod | bin | for client-side map rendering and integration testing |
| [firefox-geckodriver](https://www.ubuntuupdates.org/package/ubuntu_mozilla_security/bionic/main/base/firefox-geckodriver) | 95+ | MPL | Dockerfile | prod | bin | for client-side map rendering and integration testing |
| [pipenv](https://pypi.org/project/pipenv/) | 2024.4.0 | MIT | Dockerfile | prod | bin | to install Python dependencies |
| [node.js](https://nodejs.org/) | 22 | MIT | client/docker/Dockerfile | prod | bin | to run Layman Test Client and Timgen |
| [npm](https://www.npmjs.com/get-npm) | 10 | Artistic License 2.0 | client/docker/Dockerfile | prod | bin | to install node.js dependencies |
| [gunicorn](https://gunicorn.org/) | 22 | MIT | requirements.production.txt | opt | bin | as Flask production server |
| [nginx](http://nginx.org/) | 1.16 | BSD 2-Clause | docker-compose.yml | opt | bin | as production server |

### Python dependencies
| name | license | used by | env | bin or src | purpose |
| --- | --- | --- | --- | --- | --- |
| [flask](http://flask.pocoo.org/) | BSD License | Pipfile | prod | bin | to build REST API |
| [celery](https://github.com/celery/celery) | BSD 3-Clause | Pipfile | prod | bin | asynchronous task runner |
| [redis-py](https://github.com/redis/redis-py) | MIT | Pipfile | prod | bin | |
| [unidecode](https://github.com/avian2/unidecode) | GNU GPL v2 | Pipfile | prod | bin | |
| [psycopg2-binary](https://github.com/psycopg/psycopg2) | GNU LGPL | Pipfile | prod | bin | |
| [requests](https://requests.readthedocs.io/) | Apache License 2.0 | Pipfile | prod | bin | |
| [owslib](https://github.com/geopython/OWSLib) | BSD 3-Clause | Pipfile | prod | bin | |
| [jsonschema](https://github.com/python-jsonschema/jsonschema) | MIT | Pipfile | prod | bin | |
| [flower](https://github.com/mher/flower) | BSD 3-Clause | Pipfile | prod | bin | to monitor celery tasks |
| [selenium](https://www.chromium.org/) | Apache License 2.0 | Dockerfile | prod | bin | for client-side map rendering and integration testing |
| [cacheout](https://github.com/dgilland/cacheout) | MIT | Pipfile | prod | bin | |
| [kombu](https://github.com/celery/kombu) | BSD 3-Clause | Pipfile | prod | bin | messaging for celery, direct dependency only for version |
| [pycld2](https://github.com/aboSamoor/pycld2) | Apache License 2.0 | Pipfile | prod | bin | detecting language for metadata |
| [lxml](https://lxml.de) | BSD 3-Clause | python3-lxml | prod | bin | |
| [watchdog](https://github.com/gorakhargosh/watchdog) | Apache License 2.0 | Pipfile | dev | bin | |
| [pytest](https://pytest.org/) | MIT License | Pipfile | test | bin | |
| [flake8](https://flake8.pycqa.org/) | MIT | Pipfile | test | bin | code style checker |
| [pycodestyle](https://pycodestyle.pycqa.org/) | MIT | Pipfile | test | bin | code style checker |
| [pylint](https://github.com/pylint-dev/pylint) | GNU GPL v2 | Pipfile | test | bin | code style checker |
| [autopep8](https://github.com/hhatto/autopep8) | MIT | Pipfile | test | bin | to automatically fix code style |
| [pytest-rerunfailures](https://github.com/pytest-dev/pytest-rerunfailures) | MPL | Pipfile | test | bin | to automatically rerun flaky tests |
| [pytest-timeout](https://pypi.org/project/pytest-timeout/) | MIT | Pipfile | test | bin | to automatically stop tests after given timeout |
| [pillow](https://github.com/python-pillow/Pillow) | HPND | Pipfile | test | bin | to ensure similarity of images |
| [jsonpath-ng](https://github.com/h2non/jsonpath-ng) | HPND | Pipfile | test | bin | to query JSON files |

### Node.js dependencies
| name | license | used by | env | bin or src | purpose |
| --- | --- | --- | --- | --- | --- |
| [layman-test-client](https://github.com/LayerManager/layman-test-client) | GNU GPL v3 | client/docker/Dockerfile | opt | bin | to demonstrate communication with REST API |
| [openlayers](https://openlayers.org/) | BSD 2-Clause | timgen/package.json | prod | bin | for client-side map rendering in Timgen |
| [express](https://expressjs.com/) | MIT | timgen/package.json | prod | bin | as HTTP server for Timgen |
| [http-proxy-middleware](https://github.com/chimurai/http-proxy-middleware) | MIT | timgen/package.json | prod | bin | for proxying Timgen requests |
| [file-saver](https://www.npmjs.com/package/file-saver) | MIT | timgen/package.json | prod | bin | for saving images in Timgen |

## Wagtail extensions
| name | license | used by | env | bin or src | purpose |
| --- | --- | --- | --- | --- | --- |
| [Wagtail CRX (CodeRed Extensions)](https://docs.coderedcorp.com/wagtail-crx/) | BSD 3-Clause | deps/wagtail/laymanportal/requirements.txt | opt | bin | to be consistent with production usage |
| [django-allauth](https://github.com/pennersr/django-allauth) | MIT | deps/wagtail/laymanportal/requirements.txt | opt | bin | to be consistent with production usage |
| [django-oauth-toolkit](https://github.com/django-oauth/django-oauth-toolkit) | BSD 2-Clause | deps/wagtail/laymanportal/requirements.txt | opt | bin | as OAuth2 provider |

## Other dependencies

| name | license | used by | env | bin or src | purpose |
| --- | --- | --- | --- | --- | --- |
| [python3-pip](https://packages.debian.org/jessie/python3-pip) | MIT | Dockerfile | prod | bin | for installing pipenv and gunicorn |
| [hslayers-ng](https://github.com/hslayers/hslayers-ng) | MIT | schema.draft-07.json | prod | src | |
| [postgis_restore.pl](https://github.com/postgis/postgis/blob/3.1.2/utils/postgis_restore.pl.in) | GNU GPL v2 | upgrade_v1_14_postgis_restore.pl | upgrade | src | |
| [libxml2](http://xmlsoft.org/) | MIT | python3-lxml | prod | bin | |
| [libxslt1.1](http://xmlsoft.org/libxslt/) | MIT | python3-lxml | prod | bin | |
| [gdal/docker](https://github.com/OSGeo/gdal/tree/master/docker) | MIT License | Dockerfile | prod | bin | |
| [docker.osgeo.org/geoserver](https://github.com/geoserver/docker) | GNU GPL v2 | docker-compose.yml | dev | bin | |
| [layermanager/qgis-server](https://github.com/LayerManager/docker-qgis-server) | GNU GPL v3 | docker-compose.yml | dev | bin | |
| [layermanager/docker-postgis](https://github.com/layermanager/docker-postgis) | MIT | docker-compose.yml | dev | bin | |
| [jirikcz/micka](https://github.com/LayerManager/docker-micka) | GNU GPL v3 | docker-compose.yml | prod-external | bin | |
| [samtux/micka](https://github.com/samtux/docker-micka) | GNU GPL v3 | jirikcz/micka | prod-external | src | |
| [docker-library/redis](https://github.com/redis/docker-library-redis) | BSD 3-Clause | docker-compose.yml | prod | bin | |
| [plantuml/plantuml](https://hub.docker.com/r/plantuml/plantuml) | GNU GPL v3 | Makefile | dev | bin | render PlantUML images |
