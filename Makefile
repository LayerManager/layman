.PHONY: download-gs-datadir reset-gs-datadir layman-build

reset-empty-gs-datadir-dev:
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman_dev bash /code/src/reset-empty-gs-datadir.sh

reset-layman-gs-datadir-dev:
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman_dev bash /code/src/reset-layman-gs-datadir.sh

reset-test-client-dev:
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman_dev bash -c "rm -rf /code/src/layman/static/test-client && bash /code/src/ensure-test-client.sh"

layman-build-dev:
	docker-compose -f docker-compose.dev.yml build layman_dev

layman-build-production-only:
	docker-compose -f docker-compose.production.yml build layman

layman-bash:
	docker-compose -f docker-compose.dev.yml run --rm layman_dev bash

hslayers-build:
	docker-compose -f docker-compose.dev.yml build hslayers

hslayers-bash:
	docker-compose -f docker-compose.dev.yml run --rm --service-ports hslayers sh

psql:
	docker-compose -f docker-compose.dev.yml run -e PGPASSWORD=docker --entrypoint "psql -U docker -p 5432 -h db gis" --rm db

clear-data-dev:
	docker-compose -f docker-compose.dev.yml run --rm layman_dev bash -c "python3 src/clear_layman_data.py"

clear-python-cache-dev:
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman_dev bash /code/src/clear-python-cache.sh

start-layman-dev:
	docker-compose -f docker-compose.dev.yml up

start-layman-dev-d:
	docker-compose -f docker-compose.dev.yml up -d

restart-layman-dev:
	docker-compose -f docker-compose.dev.yml up --force-recreate --no-deps -d layman_dev celery_worker_dev

stop-layman-dev:
	docker-compose -f docker-compose.dev.yml rm --stop --force layman_dev celery_worker_dev

restart-layman-dev-and-build:
	docker-compose -f docker-compose.dev.yml build layman_dev
	docker-compose -f docker-compose.dev.yml up --force-recreate --no-deps -d layman_dev

restart-geoserver-dev:
	docker-compose -f docker-compose.dev.yml stop geoserver
	docker-compose -f docker-compose.dev.yml run --rm --no-deps layman bash -c "bash /code/src/reset-layman-gs-datadir.sh"
	docker-compose -f docker-compose.dev.yml up --no-deps -d geoserver

restart-celery-dev:
	docker-compose -f docker-compose.dev.yml rm -fsv flower
	docker-compose -f docker-compose.dev.yml rm -fsv celery_worker_dev
	docker-compose -f docker-compose.test.yml rm -fsv celery_worker_test
	docker-compose -f docker-compose.dev.yml rm -fsv redis
	docker-compose -f docker-compose.dev.yml up --no-deps -d redis
	docker-compose -f docker-compose.dev.yml up --no-deps -d celery_worker_dev
	docker-compose -f docker-compose.test.yml up --no-deps -d celery_worker_test
	docker-compose -f docker-compose.dev.yml up --no-deps -d flower

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
	docker-compose -f docker-compose.test.yml run --rm layman_test

test-dev:
	docker-compose -f docker-compose.test.yml up --force-recreate --no-deps -d celery_worker_test
	docker-compose -f docker-compose.test.yml run --rm layman_test

test-bash:
	docker-compose -f docker-compose.test.yml run --rm layman_test bash

redis-test-bash:
	docker-compose -f docker-compose.dev.yml exec redis redis-cli -h redis -p 6379 -n 15

stop-all-docker-containers:
	docker stop $$(docker ps -q)

