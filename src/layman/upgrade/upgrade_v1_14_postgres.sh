#!/bin/bash
set -ex

sudo rm -rf tmp/v1_14_db_migration
mkdir -p tmp/v1_14_db_migration

sudo mv deps/postgresql/data deps/postgresql/data_10

docker run -d -e USERNAME=docker -e PASS=docker -e ALLOW_IP_RANGE=0.0.0.0/0 -e POSTGRES_TEMPLATE_EXTENSIONS=true -v ${PWD}/deps/postgresql/data_10:/var/lib/postgresql -v ${PWD}/tmp/v1_14_db_migration:/tmp/tmp_migration --name postgres_migration_10 kartoza/postgis:10.0-2.4 postgres
docker run -d -e POSTGRES_USER=docker -e POSTGRES_PASSWORD=docker -e POSTGRES_DB=gis -v ${PWD}/deps/postgresql/data:/var/lib/postgresql/data -v ${PWD}/tmp/v1_14_db_migration:/tmp/tmp_migration -v ${PWD}/src:/code/src --name postgres_migration_13 layermanager/postgis:13.3-3.1-20210608 postgres

sleep 3
docker exec postgres_migration_13 bash -c "apk add perl"
docker exec postgres_migration_13 bash -c "chmod -R 777 /tmp/tmp_migration/"

docker exec -u postgres postgres_migration_10 bash -c "echo \"CREATE OR REPLACE FUNCTION _prime_schema.my_unaccent(text) RETURNS tsvector LANGUAGE SQL IMMUTABLE AS 'SELECT to_tsvector(public.unaccent(\\\$1))';\" | psql gis"

docker exec -u postgres postgres_migration_10 bash -c "pg_dump -Fc -b -v -f /tmp/tmp_migration/backup_10_1 gis"
docker exec postgres_migration_13 bash -c "/code/src/layman/upgrade/upgrade_v1_14_dump_cleanup.sh /tmp/tmp_migration/backup_10_1 /tmp/tmp_migration/backup_10_1_postgis"
docker exec -e PGPASSWORD=docker postgres_migration_13 bash -c "psql -U docker gis < /tmp/tmp_migration/backup_10_1_postgis"

if [ "$( docker exec -u postgres postgres_migration_10 bash -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='hsrs_micka6'\"" )" = '1' ]
then
    docker exec -u postgres postgres_migration_10 bash -c "pg_dump -Fc -b -v -f /tmp/tmp_migration/backup_10_1_micka hsrs_micka6"
    docker exec postgres_migration_13 bash -c "/code/src/layman/upgrade/upgrade_v1_14_dump_cleanup.sh /tmp/tmp_migration/backup_10_1_micka /tmp/tmp_migration/backup_10_1_micka_postgis"

    docker exec -e PGPASSWORD=docker postgres_migration_13 bash -c "echo 'create database hsrs_micka6 template template_postgis' | psql -U docker gis"
    docker exec -e PGPASSWORD=docker postgres_migration_13 bash -c "psql -U docker hsrs_micka6 < /tmp/tmp_migration/backup_10_1_micka_postgis"
else
    echo "Database 'hsrs_micka6' does not exist"
fi

docker stop postgres_migration_10
docker stop postgres_migration_13
docker rm postgres_migration_10
docker rm postgres_migration_13
sudo rm -rf deps/postgresql/data_10
sudo rm -rf tmp/v1_14_db_migration
