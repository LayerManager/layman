
## Main dependencies

| name | version | license | used by | env | bin or src | note |
| --- | --- | --- | --- | --- | --- | --- |
| [python](http://www.gdal.org/) | 3.5 | Python Software Foundation License | - | prod | bin | |
| [flask](http://flask.pocoo.org/) | 1.0.2 | BSD License | - | prod | bin | |
| [postgresql](https://www.postgresql.org/) | 10.0 | PostgreSQL | kartoza/docker-postgis | dev | bin | |
| [postgis](https://postgis.net/) | 2.4 | GNU GPL v2 | kartoza/docker-postgis | dev | bin | |
| [geoserver](https://github.com/geoserver/geoserver) | 2.13.0 | GNU GPL v2 | kartoza/docker-geoserver | dev | bin | |
| [gdal](http://www.gdal.org/) | 2.3.0 | MIT License | geographicags/docker-gdal2 | dev | bin | |

## Other dependencies

| name | license | used by | env | bin or src | note |
| --- | --- | --- | --- | --- | --- |
| [pytest](https://pytest.org/) | MIT License | - | test | bin | requirements.txt |
| [kartoza/docker-geoserver](https://github.com/kartoza/docker-geoserver) | GNU GPL v2 | - | dev | src | docker-compose.yml |
| [geographicags/docker-gdal2](https://github.com/GeographicaGS/Docker-GDAL2) | MIT License | - | dev | bin | used as docker image |
| [kartoza/docker-geoserver](https://github.com/kartoza/docker-geoserver) | GNU GPL v2 | - | dev | bin | used as docker image |
| [kartoza/docker-postgis](https://github.com/kartoza/docker-postgis) | - | kartoza/docker-geoserver | dev | bin | used as docker image |
| [docker-library/tomcat](https://github.com/docker-library/tomcat) | Apache License 2.0 | kartoza/docker-geoserver | dev | bin | used as docker image |
| [apache/tomcat](http://tomcat.apache.org/) | Apache License 2.0 | docker-library/tomcat | dev | bin | |
| [docker-library/openjdk](https://github.com/docker-library/openjdk) | MIT License | docker-library/tomcat | dev | bin | used as docker image |
| [java/openjdk](http://openjdk.java.net/) | GNU GPL v2 | docker-library/openjdk | dev | bin | |
| [docker-library/buildpack-deps](https://github.com/docker-library/buildpack-deps) | MIT License | docker-library/openjdk | dev | bin | used as docker image |
| [debuerreotype/docker-debian-artifacts](https://github.com/debuerreotype/docker-debian-artifacts) | Apache License 2.0 | docker-library/buildpack-deps, kartoza/docker-postgis | dev | bin | used as docker image |
| [debian](https://www.debian.org/) | GNU GPL mostly | debuerreotype/docker-debian-artifacts | dev | bin | |
