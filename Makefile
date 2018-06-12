.PHONY: download-gs-datadir reset-gs-datadir layman-build

download-gs-datadir: guard-GS_VERSION
	mkdir -p tmp/geoserver/${GS_VERSION}/
	rm -rf tmp/geoserver/${GS_VERSION}/*
	wget -O tmp/geoserver/${GS_VERSION}/geoserver.zip http://sourceforge.net/projects/geoserver/files/GeoServer/${GS_VERSION}/geoserver-${GS_VERSION}-war.zip
	unzip tmp/geoserver/${GS_VERSION}/geoserver.zip -d tmp/geoserver/${GS_VERSION}/
	mkdir -p tmp/geoserver/${GS_VERSION}/geoserver
	unzip tmp/geoserver/${GS_VERSION}/geoserver.war -d tmp/geoserver/${GS_VERSION}/geoserver

reset-gs-datadir: guard-GS_VERSION
	mkdir -p geoserver_data
	rm -rf geoserver_data/*
	cp -r tmp/geoserver/${GS_VERSION}/geoserver/data/* geoserver_data
	chmod -R a+rwx geoserver_data

layman-build:
	docker build -t "layman:latest" ./layman

layman-bash:
	docker run -it --rm layman bash

guard-%:
	@ if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi
