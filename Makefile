.PHONY: test

start-demo:
	docker-compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml up --force-recreate postgresql geoserver redis layman celery_worker flower hslayers layman_client nginx

start-demo-d:
	docker-compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml up -d --force-recreate postgresql geoserver redis layman celery_worker flower hslayers layman_client nginx

start-demo-only-d:
	docker-compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml up -d --force-recreate --no-deps layman celery_worker flower hslayers layman_client

stop-demo:
	docker-compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml stop

start-demo-with-optional-deps:
	docker-compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml up --force-recreate

start-demo-with-optional-deps-d:
	docker-compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml up -d --force-recreate

build-demo:
	docker-compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml build layman

deps-start:
	docker-compose -f docker-compose.deps.yml up --force-recreate -d

deps-stop:
	docker-compose -f docker-compose.deps.yml stop

deps-remove-data:
	docker-compose -f docker-compose.deps.yml rm -fsv
	rm -rf deps/*/data

start-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --force-recreate

start-dev-d:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --force-recreate -d

stop-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml stop

start-dev-only:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml rm -fsv layman_dev celery_worker_dev flower hslayers layman_client
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up layman_dev celery_worker_dev flower hslayers layman_client

start-dev-only-d:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml rm -fsv layman_dev celery_worker_dev flower hslayers layman_client
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up -d layman_dev celery_worker_dev flower hslayers layman_client

stop-dev-only:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml stop layman_dev celery_worker_dev flower hslayers layman_client

restart-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --force-recreate --no-deps -d layman_dev celery_worker_dev

rebuild-and-restart-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml build layman_dev
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --force-recreate --no-deps -d layman_dev

restart-celery-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml rm -fsv layman_client
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml rm -fsv flower
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml rm -fsv celery_worker_dev
	docker-compose -f docker-compose.deps.yml -f docker-compose.test.yml rm -fsv celery_worker_test
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml rm -fsv layman_dev
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml rm -fsv redis
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --no-deps -d redis
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --no-deps -d layman_dev
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --no-deps -d celery_worker_dev
	docker-compose -f docker-compose.deps.yml -f docker-compose.test.yml up --no-deps -d celery_worker_test
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --no-deps -d flower
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --no-deps -d layman_client

prepare-dirs:
	mkdir -p layman_data layman_data_test tmp

build-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml build --force-rm layman_dev

rebuild-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml build --no-cache --force-rm layman_dev

bash:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml run --rm layman_dev bash

bash-root:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml run --rm -u root layman_dev bash

bash-exec:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml exec layman_dev bash

bash-demo:
	docker-compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml run --rm layman bash

bash-demo-root:
	docker-compose -f docker-compose.deps.demo.yml -f docker-compose.demo.yml run --rm -u root layman bash

clear-data-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml run --rm layman_dev bash -c "python3 src/clear_layman_data.py"

clear-python-cache-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml run --rm --no-deps layman_dev bash /code/src/clear-python-cache.sh

hslayers-build:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml build hslayers

hslayers-restart:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml build hslayers
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --force-recreate --no-deps -d hslayers

hslayers-bash:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml run --rm hslayers sh

client-build:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml build layman_client
	docker-compose -f docker-compose.deps.yml -f docker-compose.test.yml build layman_client_test

client-restart:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml build layman_client
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml up --force-recreate --no-deps -d layman_client
	docker-compose -f docker-compose.deps.yml -f docker-compose.test.yml up --force-recreate --no-deps -d layman_client_test

client-bash:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml run --rm layman_client sh

client-bash-root:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml run --rm -u root layman_client sh

client-bash-exec-root:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml exec -u root layman_client sh

test:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml build layman_dev
	docker-compose -f docker-compose.deps.yml -f docker-compose.test.yml run --rm --name layman_test_run_1 layman_test

test-dev:
	docker-compose -f docker-compose.deps.yml -f docker-compose.test.yml up --force-recreate --no-deps -d celery_worker_test
	docker-compose -f docker-compose.deps.yml -f docker-compose.test.yml run --rm --name layman_test_run_1 layman_test

test-bash:
	docker-compose -f docker-compose.test.yml run --rm layman_test bash

test-wait-for-deps:
	docker-compose -f docker-compose.deps.yml rm -fsv
	docker-compose -f docker-compose.deps.yml up --force-recreate -d
	docker-compose -f docker-compose.deps.yml -f docker-compose.test.yml run --rm layman_test bash -c "python3 src/wait_for_deps.py"

postgresql-psql:
	docker-compose -f docker-compose.deps.yml run -e PGPASSWORD=docker --entrypoint "psql -U docker -p 5432 -h postgresql gis" --rm postgresql

redis-cli-db:
	docker-compose -f docker-compose.deps.yml exec redis redis-cli -h redis -p 6379 -n 0

redis-cli-test-db:
	docker-compose -f docker-compose.deps.yml exec redis redis-cli -h redis -p 6379 -n 15

redis-cli-client-dev-db:
	docker-compose -f docker-compose.deps.yml exec redis redis-cli -h redis -p 6379 -n 1

redis-cli-client-test-db:
	docker-compose -f docker-compose.deps.yml exec redis redis-cli -h redis -p 6379 -n 13

redis-cli-client-standalone-db:
	docker-compose -f docker-compose.deps.yml exec redis redis-cli -h redis -p 6379 -n 14

geoserver-reset-default-layman-datadir:
	docker-compose -f docker-compose.deps.yml run --rm --no-deps geoserver bash /geoserver_code/reset-default-layman-datadir.sh

geoserver-restart:
	docker-compose -f docker-compose.deps.yml rm -fsv geoserver
	docker-compose -f docker-compose.deps.yml run --rm --no-deps geoserver bash /geoserver_code/reset-default-layman-datadir.sh
	docker-compose -f docker-compose.deps.yml up --no-deps -d geoserver

geoserver-reset-empty-datadir:
	docker-compose -f docker-compose.deps.yml run --rm --no-deps geoserver bash /geoserver_code/reset-empty-datadir.sh

geoserver-bash:
	docker-compose -f docker-compose.deps.yml run --rm --no-deps geoserver bash

liferay-introspect:
	curl 'http://localhost:8082/o/oauth2/introspect' --data 'client_id=id-353ab09c-f117-f2d5-d3a3-85cfb89e6746&client_secret=secret-d31a82c8-3e73-1058-e38a-f9191f7c2014&token=...'

liferay-refresh:
	curl 'http://localhost:8082/o/oauth2/token' --data 'grant_type=refresh_token&client_id=id-353ab09c-f117-f2d5-d3a3-85cfb89e6746&client_secret=secret-d31a82c8-3e73-1058-e38a-f9191f7c2014&refresh_token=...'

liferay-userprofile:
	curl -H "Authorization: Bearer ..." http://localhost:8082/api/jsonws/user/get-current-user

get-current-user:
	curl -H "Authorization: Bearer ..." -H "AuthorizationIssUrl: ..." http://localhost:8000/rest/current-user

liferay-bash:
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml exec liferay bash

liferay-export-settings:
	rm -f deps/liferay/transit/*
	docker-compose -f docker-compose.deps.yml -f docker-compose.dev.yml exec liferay bash -c "cd data/hypersonic; cp lportal.log /etc/liferay/tmp/; cp lportal.properties /etc/liferay/tmp/; cp lportal.script /etc/liferay/tmp/"
	rm -f deps/liferay/sample/hypersonic/*
	mv -f deps/liferay/transit/* deps/liferay/sample/hypersonic/

liferay-start:
	docker-compose -f docker-compose.deps.yml up --force-recreate -d liferay

liferay-stop:
	docker-compose -f docker-compose.deps.yml stop liferay

stop-all-docker-containers:
	docker stop $$(docker ps -q)

remove-all-docker-containers:
	docker rm $$(docker ps -aq)

stop-and-remove-all-docker-containers:
	docker stop $$(docker ps -q)
	docker rm $$(docker ps -aq)

github-purge-cache:
	if ! [ -f tmp/github-purge.sh ] ; then \
		curl -o tmp/github-purge.sh -LO https://raw.githubusercontent.com/mpyw/hub-purge/master/hub-purge.sh ; \
	fi
	chmod +x tmp/github-purge.sh
	./tmp/github-purge.sh ${ARGS}
