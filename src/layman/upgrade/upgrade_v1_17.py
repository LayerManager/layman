import logging

from db import util as db_util
from layman import settings, util as layman_util
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_file_type():
    logger.info(f'    Alter DB prime schema for file type')

    statement = f'''
    DO $$ BEGIN
        CREATE TYPE {DB_SCHEMA}.enum_file_type AS ENUM ('vector', 'raster', 'unknown');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
        ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS
        file_type {DB_SCHEMA}.enum_file_type;'''

    db_util.run_statement(statement)


def adjust_publications_file_type():
    logger.info(f'    Adjust file type of publications')
    query = f'''select w.name, p.type, p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
    ;'''
    publications = db_util.run_query(query, (LAYER_TYPE, ))

    for workspace, publ_type, publication in publications:
        file_type = None
        logger.info(f'    Adjust file type of {publ_type} {workspace}.{publication}')
        file_type = layman_util.get_publication_info(workspace, publ_type, publication,
                                                     context={'keys': ['file']})['file']['file_type']

        query = f'''update {DB_SCHEMA}.publications set
        file_type = %s
        where type = %s
          and name = %s
          and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
        params = (file_type, publ_type, publication, workspace,)
        db_util.run_statement(query, params)

    logger.info(f'    Adjusting publications file type DONE')


def adjust_db_publication_file_type_constraint():
    statement = f'alter table {DB_SCHEMA}.publications add constraint file_type_with_publ_type_check CHECK ' \
                f'((type = %s AND file_type IS NULL) OR (type = %s AND file_type IS NOT NULL));'
    db_util.run_statement(statement, (MAP_TYPE, LAYER_TYPE))
