import pytest

from layman import app, settings
from layman.common.prime_db_schema import util as db_util
from . import consts
from .. import upgrade
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def test_upgrade_run():
    with app.app_context():
        upgrade.upgrade()


@pytest.mark.parametrize('mig_type, version_to_test', [
    (consts.MIGRATION_TYPE_SCHEMA, (1, 11, 0, 0), ),
    (consts.MIGRATION_TYPE_DATA, (1, 11, 0, 0),),
])
def test_check_version_upgradeability(mig_type, version_to_test):
    with app.app_context():
        current_version = upgrade.get_current_version(mig_type)
        upgrade.check_version_upgradeability()

        upgrade.set_current_migration_version(mig_type, version_to_test)
        with pytest.raises(AssertionError):
            upgrade.check_version_upgradeability()

        upgrade.set_current_migration_version(mig_type, current_version)
        upgrade.check_version_upgradeability()


@pytest.fixture()
def preserve_data_version_table():
    copy_table = f'''create table {DB_SCHEMA}.data_version_backup as table {DB_SCHEMA}.data_version;'''
    with app.app_context():
        db_util.run_statement(copy_table)
    yield
    copy_table_back = f'''
    DROP TABLE IF EXISTS {DB_SCHEMA}.data_version;
    create table {DB_SCHEMA}.data_version as table {DB_SCHEMA}.data_version_backup;
    DROP TABLE IF EXISTS {DB_SCHEMA}.data_version_backup;
    '''
    with app.app_context():
        db_util.run_statement(copy_table_back)


@pytest.mark.usefixtures('preserve_data_version_table')
@pytest.mark.parametrize('sql_command, expected_value, migration_type', [
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
