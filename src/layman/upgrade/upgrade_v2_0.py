import logging

from db import util as db_util
from layman import settings
from layman.layer import LAYER_TYPE
from layman.layer.geoserver import wms as gs_wms
from layman.map import MAP_TYPE
from layman.map.filesystem import input_file

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_description():
    logger.info(f'    Alter DB prime schema for description')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS
    description varchar(1024) default null;'''
    db_util.run_statement(statement)


def adjust_publications_description():
    logger.info(f'    Adjust description of publications')
    query = f'''select w.name, p.type, p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    ;'''
    publications = db_util.run_query(query)

    for workspace, publ_type, publication in publications:
        logger.info(f'    Adjust description of {publ_type} {workspace}.{publication}')
        get_info = {LAYER_TYPE: gs_wms.get_layer_info,
                    MAP_TYPE: input_file.get_map_info,
                    }[publ_type]
        description = get_info(workspace, publication)['description']

        query = f'''update {DB_SCHEMA}.publications set
        description = %s
        where type = %s
          and name = %s
          and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
        params = (description, publ_type, publication, workspace,)
        db_util.run_statement(query, params)

    logger.info(f'    Adjusting publications description DONE')
