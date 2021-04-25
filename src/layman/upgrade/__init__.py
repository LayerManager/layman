import logging
import psycopg2

from db import util as db_util
from layman.upgrade import upgrade_v1_8, upgrade_v1_9, upgrade_v1_10, upgrade_v1_12, upgrade_v1_13
from layman import settings
from . import consts

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

logger = logging.getLogger(__name__)

MIGRATIONS = {
    consts.MIGRATION_TYPE_SCHEMA: [
        ((1, 9, 0), [  # includes also data migrations
            upgrade_v1_9.initialize_data_versioning,
            upgrade_v1_9.geoserver_everyone_rights_repair,
            upgrade_v1_9.geoserver_remove_users_for_public_workspaces,
        ]),
        ((1, 10, 0), [  # includes also data migrations
            upgrade_v1_10.alter_schema,
            upgrade_v1_10.check_workspace_names,
            upgrade_v1_10.migrate_layers_to_wms_workspace,
            upgrade_v1_10.migrate_maps_on_wms_workspace,
            upgrade_v1_10.migrate_metadata_records,
            upgrade_v1_10.migrate_input_sld_directory_to_input_style,
            upgrade_v1_10.update_style_type_in_db,
        ]),
        ((1, 12, 0), [
            upgrade_v1_12.adjust_db_for_schema_migrations,
            upgrade_v1_12.adjust_prime_db_schema_for_fulltext_search,
            upgrade_v1_12.adjust_prime_db_schema_for_last_change_search,
            upgrade_v1_12.adjust_prime_db_schema_for_bbox_search,
        ]),
        ((1, 13, 0), [
            upgrade_v1_13.rename_users_directory,
        ]),
    ],
    consts.MIGRATION_TYPE_DATA: [
        ((1, 12, 0), [
            upgrade_v1_12.adjust_data_for_last_change_search,
            upgrade_v1_12.migrate_layer_metadata,
            upgrade_v1_12.adjust_data_for_bbox_search,
        ]),
    ],
}


def get_max_data_version(migration_type):
    max_migration = max(MIGRATIONS[migration_type], key=lambda x: x[0])
    return max_migration[0] + (len(max_migration[1]) - 1, )


def get_current_version(migration_type):
    current_version = None
    try:
        sql_select = f'''select major_version, minor_version, patch_version, migration
        from {DB_SCHEMA}.data_version
        where migration_type = '{migration_type}';'''
        sql_result = db_util.run_query(sql_select, encapsulate_exception=False)
        row_count = len(sql_result)
        if row_count == 1:
            current_version = sql_result[0]
        elif row_count == 0:
            current_version = (-1, -1, -1, -1)
        else:
            assert row_count == 1
    except psycopg2.errors.UndefinedTable:  # pylint: disable=no-member
        current_version = (-1, -1, -1, -1)
    except psycopg2.errors.UndefinedColumn:  # pylint: disable=no-member
        assert migration_type == consts.MIGRATION_TYPE_SCHEMA
        sql_select = f'''select major_version, minor_version, patch_version, migration
        from {DB_SCHEMA}.data_version;'''
        sql_result = db_util.run_query(sql_select, encapsulate_exception=False)
        row_count = len(sql_result)
        assert row_count == 1
        current_version = sql_result[0]
    return current_version


def set_current_migration_version(migration_type, version):
    try:
        sql_insert = f'''update {DB_SCHEMA}.data_version set
            major_version = %s,
            minor_version = %s,
            patch_version = %s,
            migration = %s
        where migration_type = '{migration_type}';'''
        db_util.run_statement(sql_insert, version, encapsulate_exception=False)
    except psycopg2.errors.UndefinedColumn:  # pylint: disable=no-member
        assert migration_type == consts.MIGRATION_TYPE_SCHEMA

        sql_select = f'''select count(*) from {DB_SCHEMA}.data_version;'''
        sql_result = db_util.run_query(sql_select)
        assert sql_result[0][0] == 1

        sql_insert = f'''update {DB_SCHEMA}.data_version set
            major_version = %s,
            minor_version = %s,
            patch_version = %s,
            migration = %s;'''
        db_util.run_statement(sql_insert, version)


def run_migrations(migration_type):
    current_data_version = get_current_version(migration_type)
    max_data_version = get_max_data_version(migration_type)
    logger.info(f'  Current {migration_type} version = {current_data_version}, Maximum {migration_type} version = {max_data_version}')
    migration_list_full = [(version + (index,), migration, )
                           for version, migration_list in MIGRATIONS[migration_type]
                           for index, migration in enumerate(migration_list)
                           if version + (index,) > current_data_version]
    migration_list_full.sort(key=lambda x: x[0])
    for version, migration in migration_list_full:
        logger.info(f'    Starting migration #{version[3]} for release v{version[0]}.{version[1]}.{version[2]}: {migration}')
        migration()
        set_current_migration_version(migration_type, version)

    final_data_version = get_current_version(migration_type)
    assert final_data_version == max_data_version, (final_data_version, max_data_version)
    logger.info(f'  Checking all upgrades DONE, final {migration_type} version = {final_data_version}')


def upgrade():
    logger.info(f'Checking all upgrades')
    if upgrade_v1_8.older_than_1_8():
        upgrade_v1_8.upgrade_1_8()

    run_migrations(consts.MIGRATION_TYPE_SCHEMA)
    run_migrations(consts.MIGRATION_TYPE_DATA)
    logger.info(f'Done all upgrades')
