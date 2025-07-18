import logging

from db import util as db_util
from layman.upgrade import upgrade_v1_8, upgrade_v1_9, upgrade_v1_10, upgrade_v1_12, upgrade_v1_16, upgrade_v1_17, upgrade_v1_18, \
    upgrade_v1_20, upgrade_v1_21, upgrade_v1_22, upgrade_v1_23, upgrade_v2_0, upgrade_v3_0
from layman import settings
from . import consts

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

logger = logging.getLogger(__name__)


MIGRATION_TYPES = [consts.MIGRATION_TYPE_SCHEMA, consts.MIGRATION_TYPE_DATA]

MIN_UPGRADEABLE_VERSION = {
    consts.MIGRATION_TYPE_DATA: (2, 0, 0, 0),
    consts.MIGRATION_TYPE_SCHEMA: (2, 0, 0, 0),
    consts.MORE_INFO_VERSION: '3.0.0',
}


MIGRATIONS = {
    consts.MIGRATION_TYPE_SCHEMA: [
        ((3, 0, 0), [lambda: logger.info("3.0.0 schema – no structural changes"),]),
    ],
    consts.MIGRATION_TYPE_DATA: [
        ((3, 0, 0), [
            upgrade_v3_0.migrate_map_graphic_urls,
            upgrade_v3_0.migrate_layer_graphic_urls,
        ]),
    ],
}


def is_new_installation():
    query = "SELECT count(*) FROM information_schema.schemata WHERE schema_name = %s;"
    count = db_util.run_query(query, (DB_SCHEMA, ))[0][0]
    return count == 0


def run_db_init():
    logger.info(f'  DB init')
    upgrade_v1_8.upgrade_1_8()
    upgrade_v1_9.initialize_data_versioning()
    upgrade_v1_10.alter_schema()
    upgrade_v1_10.update_style_type_in_db()
    upgrade_v1_12.adjust_db_for_schema_migrations()
    upgrade_v1_12.adjust_prime_db_schema_for_fulltext_search()
    upgrade_v1_12.adjust_prime_db_schema_for_last_change_search()
    upgrade_v1_12.adjust_prime_db_schema_for_bbox_search()
    upgrade_v1_16.adjust_db_for_srid()
    upgrade_v1_17.adjust_db_for_file_type()
    upgrade_v1_18.adjust_db_for_image_mosaic()
    upgrade_v1_20.adjust_db_for_table_uri()
    upgrade_v1_20.rename_file_type_to_geodata_type()
    upgrade_v1_21.adjust_db_for_wfs_wms_status()
    upgrade_v1_22.create_map_layer_relation_table()
    upgrade_v1_23.adjust_db_for_roles()
    upgrade_v1_23.restrict_workspace_name_length()
    upgrade_v1_23.create_role_service_schema()
    upgrade_v1_23.remove_right_types_table()

    upgrade_v1_16.adjust_db_publication_srid_constraint()
    upgrade_v1_17.adjust_db_publication_file_type_constraint()
    upgrade_v1_21.ensure_sub_uniqueness()
    upgrade_v1_22.ensure_issuer_sub_uniqueness()

    upgrade_v2_0.adjust_db_for_description()
    upgrade_v2_0.adjust_db_for_map_layer_relation()
    upgrade_v2_0.adjust_db_for_created_at()
    upgrade_v2_0.ensure_gs_workspaces_and_stores()
    upgrade_v2_0.ensure_layers_db_schema()
    upgrade_v2_0.adjust_publications_created_at()
    upgrade_v2_0.adjust_map_layer_data()

    for mig_type in MIGRATION_TYPES:
        set_current_migration_version(mig_type, MIN_UPGRADEABLE_VERSION[mig_type])


def check_version_upgradeability():
    more_info_version = MIN_UPGRADEABLE_VERSION[consts.MORE_INFO_VERSION]
    for mig_type in MIGRATION_TYPES:
        current_version = get_current_version(mig_type)
        min_version = MIN_UPGRADEABLE_VERSION[mig_type]
        assert current_version >= min_version, \
            f'Layman is not able to upgrade from {mig_type} version {current_version}. ' \
            f'Minimum upgradeable version is {min_version}. ' \
            f'More info in Changelog for release v{more_info_version}: ' \
            f'https://github.com/LayerManager/layman/blob/v{more_info_version}/CHANGELOG.md#upgrade-requirements'


def get_max_data_version(migration_type):
    max_migration = max(MIGRATIONS[migration_type], key=lambda x: x[0])
    return max_migration[0] + (len(max_migration[1]) - 1, )


def get_current_version(migration_type):
    sql_select = f'''select major_version, minor_version, patch_version, migration
    from {DB_SCHEMA}.data_version
    where migration_type = '{migration_type}';'''
    sql_result = db_util.run_query(sql_select, encapsulate_exception=False)
    row_count = len(sql_result)
    assert row_count == 1
    current_version = sql_result[0]
    return current_version


def set_current_migration_version(migration_type, version):
    sql_insert = f'''update {DB_SCHEMA}.data_version set
        major_version = %s,
        minor_version = %s,
        patch_version = %s,
        migration = %s
    where migration_type = '{migration_type}';'''
    db_util.run_statement(sql_insert, version, encapsulate_exception=False)


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

    if is_new_installation():
        run_db_init()
    check_version_upgradeability()
    run_migrations(consts.MIGRATION_TYPE_SCHEMA)
    run_migrations(consts.MIGRATION_TYPE_DATA)
    logger.info(f'Done all upgrades')
