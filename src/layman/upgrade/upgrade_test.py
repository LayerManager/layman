import pytest

from layman import upgrade, app, settings
from layman.common.prime_db_schema import util as db_util
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def test_upgrade_run():
    with app.app_context():
        upgrade.upgrade()


@pytest.mark.parametrize('sql_command, expected_value', [
    (f'''DROP TABLE IF EXISTS {DB_SCHEMA}.data_version''', (-1, -1, -1, -1)),
    (f'''DROP TABLE IF EXISTS {DB_SCHEMA}.data_version; CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.data_version
        (
            major_version integer not null,
            minor_version integer not null,
            patch_version integer not null,
            migration integer not null
        )
        TABLESPACE pg_default;''', (-1, -1, -1, -1)),
    (f'''DROP TABLE IF EXISTS {DB_SCHEMA}.data_version; CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.data_version
        (
            major_version integer not null,
            minor_version integer not null,
            patch_version integer not null,
            migration integer not null
        )
        TABLESPACE pg_default;
        insert into {DB_SCHEMA}.data_version (major_version, minor_version, patch_version, migration) values (1, 9, 0, 0); commit;''', (1, 9, 0, 0)),
])
def test_get_current_data_version(sql_command, expected_value):
    with app.app_context():
        db_util.run_statement(sql_command)
        currrent_data_version = upgrade.get_current_data_version()
        assert currrent_data_version == expected_value
