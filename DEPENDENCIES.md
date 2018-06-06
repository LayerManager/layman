
| name | license | wrapped by | env | bin or src | note |
| --- | --- | --- | --- | --- | --- |
| [kartoza/docker-geoserver](https://github.com/kartoza/docker-geoserver) | GNU GPL v2 | - | dev | src | docker-compose.yml |
| [kartoza/docker-geoserver](https://github.com/kartoza/docker-geoserver) | GNU GPL v2 | - | dev | bin | used as docker image |
| [geoserver/geoserver](https://github.com/geoserver/geoserver) | GNU GPL v2 | kartoza/docker-geoserver | dev | bin | |
| [docker-library/tomcat](https://github.com/docker-library/tomcat) | Apache License 2.0 | kartoza/docker-geoserver | dev | bin | used as docker image |
| [apache/tomcat](http://tomcat.apache.org/) | Apache License 2.0 | docker-library/tomcat | dev | bin | |
| [docker-library/openjdk](https://github.com/docker-library/openjdk) | MIT License | docker-library/tomcat | dev | bin | used as docker image |
| [java/openjdk](http://openjdk.java.net/) | GNU GPL v2 | docker-library/openjdk | dev | bin | |
| [docker-library/buildpack-deps](https://github.com/docker-library/buildpack-deps) | MIT License | docker-library/openjdk | dev | bin | used as docker image |
| [debuerreotype/docker-debian-artifacts](https://github.com/debuerreotype/docker-debian-artifacts) | Apache License 2.0 | docker-library/buildpack-deps | dev | bin | used as docker image |
| [debian](https://www.debian.org/) | GNU GPL mostly | debuerreotype/docker-debian-artifacts | dev | bin | |
