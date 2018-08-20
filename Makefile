.PHONY: download-gs-datadir reset-gs-datadir layman-build

reset-empty-gs-datadir:
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman bash /code/src/reset-empty-gs-datadir.sh

reset-layman-gs-datadir:
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman bash /code/src/reset-layman-gs-datadir.sh

layman-build:
	docker-compose build

layman-bash:
	docker-compose -f docker-compose.dev.yml run --rm layman bash

clear-data:
	docker-compose -f docker-compose.dev.yml run --rm layman bash -c "python3 src/clear_layman_data.py && python3 src/prepare_layman.py"

clear-python:
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman bash /code/src/clear-python-cache.sh

start-layman-dev:
	docker-compose -f docker-compose.dev.yml up

restart-layman-dev:
	docker-compose -f docker-compose.dev.yml build layman
	docker-compose -f docker-compose.dev.yml up --force-recreate --no-deps -d layman

restart-geoserver-dev:
	docker-compose -f docker-compose.dev.yml stop geoserver
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman bash -c "bash /code/src/reset-layman-gs-datadir.sh && python3 src/prepare_layman.py"
	docker-compose -f docker-compose.dev.yml up --no-deps -d geoserver

start-layman-production:
	docker-compose -f docker-compose.production.yml up -d

stop-layman-production:
	docker-compose -f docker-compose.production.yml stop

stop-layman-dependencies:
	docker-compose -f docker-compose.dependencies.yml stop

start-layman-production-with-dependencies:
	docker-compose -f docker-compose.dependencies.yml up -d
	docker-compose -f docker-compose.production.yml up -d

stop-layman-production-with-dependencies:
	docker-compose -f docker-compose.dependencies.yml stop
	docker-compose -f docker-compose.production.yml stop

test:
	docker-compose -f docker-compose.test.yml run --rm layman

test-bash:
	docker-compose -f docker-compose.test.yml run --rm layman bash

