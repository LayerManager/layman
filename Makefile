.PHONY: download-gs-datadir reset-gs-datadir layman-build

download-gs-datadir:
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman bash /code/src/download-gs-datadir.sh

reset-gs-datadir:
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman bash /code/src/reset-gs-datadir.sh

layman-build:
	docker-compose build

layman-bash:
	docker-compose -f docker-compose.dev.yml run --rm layman bash

clear-data:
	docker-compose -f docker-compose.dev.yml run --rm layman python3 src/layman/clear.py

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
	docker-compose -f docker-compose.test.yml run --rm layman

test-bash:
	docker-compose -f docker-compose.test.yml run --rm layman bash

