import pytest

from layman import upgrade, app, settings
from layman.common.prime_db_schema import util as db_util
from . import consts
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def test_upgrade_run():
    with app.app_context():
        upgrade.upgrade()


@pytest.mark.parametrize('sql_command, expected_value, migration_type', [
    (f'''DROP TABLE IF EXISTS {DB_SCHEMA}.data_version''', (-1, -1, -1, -1), consts.MIGRATION_TYPE_SCHEMA),
    (f'''DROP TABLE IF EXISTS {DB_SCHEMA}.data_version; CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.data_version
        (
            major_version integer not null,
            minor_version integer not null,
            patch_version integer not null,
            migration integer not null
        )
    TABLESPACE pg_default;
    insert into {DB_SCHEMA}.data_version (major_version, minor_version, patch_version, migration) values (1, 9, 0, 0);commit;
    ''', (1, 9, 0, 0), consts.MIGRATION_TYPE_SCHEMA),
    (f'''DROP TABLE IF EXISTS {DB_SCHEMA}.data_version; CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.data_version
        (
            major_version integer not null,
            minor_version integer not null,
            patch_version integer not null,
            migration integer not null,
            migration_type {DB_SCHEMA}.enum_migration_type UNIQUE NOT NULL
        )
        TABLESPACE pg_default;''', (-1, -1, -1, -1), consts.MIGRATION_TYPE_SCHEMA),
    (f'''DROP TABLE IF EXISTS {DB_SCHEMA}.data_version; CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.data_version
        (
            major_version integer not null,
            minor_version integer not null,
            patch_version integer not null,
            migration integer not null,
            migration_type {DB_SCHEMA}.enum_migration_type UNIQUE NOT NULL
        )
        TABLESPACE pg_default;''', (-1, -1, -1, -1), consts.MIGRATION_TYPE_DATA),
    (f'''DROP TABLE IF EXISTS {DB_SCHEMA}.data_version; CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.data_version
        (
            major_version integer not null,
            minor_version integer not null,
            patch_version integer not null,
            migration integer not null,
            migration_type {DB_SCHEMA}.enum_migration_type UNIQUE NOT NULL
        )
        TABLESPACE pg_default;
        insert into {DB_SCHEMA}.data_version (major_version, minor_version, patch_version, migration, migration_type) values (1, 9, 0, 0, '{consts.MIGRATION_TYPE_DATA}');commit;
        ''', (1, 9, 0, 0), consts.MIGRATION_TYPE_DATA),
    (f'''DROP TABLE IF EXISTS {DB_SCHEMA}.data_version; CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.data_version
    (
        major_version integer not null,
        minor_version integer not null,
        patch_version integer not null,
        migration integer not null,
        migration_type {DB_SCHEMA}.enum_migration_type UNIQUE NOT NULL
    )
    TABLESPACE pg_default;
    insert into {DB_SCHEMA}.data_version (major_version, minor_version, patch_version, migration, migration_type) values (1, 9, 0, 0, '{consts.MIGRATION_TYPE_SCHEMA}');commit;
    ''', (1, 9, 0, 0), consts.MIGRATION_TYPE_SCHEMA),
])
def test_get_current_version(sql_command, expected_value, migration_type):
    with app.app_context():
        db_util.run_statement(sql_command)
        currrent_data_version = upgrade.get_current_version(migration_type)
        assert currrent_data_version == expected_value
