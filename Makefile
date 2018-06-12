.PHONY: reset-gs-datadir check-env-gsversion

download-gs-datadir: check-env-gsversion
	mkdir -p tmp/geoserver/${GS_VERSION}/
	rm -rf tmp/geoserver/${GS_VERSION}/*
	wget -O tmp/geoserver/${GS_VERSION}/geoserver.zip http://sourceforge.net/projects/geoserver/files/GeoServer/${GS_VERSION}/geoserver-${GS_VERSION}-war.zip
	unzip tmp/geoserver/${GS_VERSION}/geoserver.zip -d tmp/geoserver/${GS_VERSION}/
	mkdir -p tmp/geoserver/${GS_VERSION}/geoserver
	unzip tmp/geoserver/${GS_VERSION}/geoserver.war -d tmp/geoserver/${GS_VERSION}/geoserver

reset-gs-datadir: check-env-gsversion
	mkdir -p geoserver_data
	rm -rf geoserver_data/*
	cp -r tmp/geoserver/${GS_VERSION}/geoserver/data/* geoserver_data
	chmod -R a+rwx geoserver_data

check-env-gsversion:
ifndef GS_VERSION
  $(error GS_VERSION is undefined)
endif