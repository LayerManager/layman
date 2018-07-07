.PHONY: download-gs-datadir reset-gs-datadir layman-build

download-gs-datadir: guard-GS_VERSION
	mkdir -p tmp/geoserver/${GS_VERSION}/
	rm -rf tmp/geoserver/${GS_VERSION}/*
	wget -O tmp/geoserver/${GS_VERSION}/geoserver.zip http://sourceforge.net/projects/geoserver/files/GeoServer/${GS_VERSION}/geoserver-${GS_VERSION}-war.zip
	unzip -q tmp/geoserver/${GS_VERSION}/geoserver.zip -d tmp/geoserver/${GS_VERSION}/
	mkdir -p tmp/geoserver/${GS_VERSION}/geoserver
	unzip -q tmp/geoserver/${GS_VERSION}/geoserver.war -d tmp/geoserver/${GS_VERSION}/geoserver

reset-gs-datadir: guard-GS_VERSION
	mkdir -p geoserver_data
	rm -rf geoserver_data/*
	cp -r tmp/geoserver/${GS_VERSION}/geoserver/data/* geoserver_data
	chmod -R a+rwx geoserver_data

layman-build:
	docker-compose build

layman-bash:
	docker-compose -f docker-compose.dev.yml run --rm layman bash

start-layman-dev:
	docker-compose -f docker-compose.dev.yml up

restart-layman-dev:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | sudo xargs rm -rf
	docker-compose -f docker-compose.dev.yml build layman
	docker-compose -f docker-compose.dev.yml up --force-recreate --no-deps -d layman

start-layman-production:
	docker-compose -f docker-compose.production.yml up -d

stop-layman-production:
	docker-compose -f docker-compose.production.yml stop

stop-layman-dependencies:
	docker-compose -f docker-compose.dependencies.yml stop

start-layman-production-with-dbgeoserver:
	docker-compose -f docker-compose.dependencies.yml up -d
	docker-compose -f docker-compose.production.yml up -d

stop-layman-production-with-dbgeoserver:
	docker-compose -f docker-compose.dependencies.yml stop
	docker-compose -f docker-compose.production.yml stop

test:
	docker-compose -f docker-compose.dev.yml run --rm layman pytest

guard-%:
	@ if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi
