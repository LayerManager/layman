import logging
import requests

from db import util as db_util
from layman import settings
from layman.layer import LAYER_TYPE
from layman.layer.geoserver.wms import get_wms_proxy
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
    where p.type = %s
       or p.wfs_wms_status = %s
    ;'''
    publications = db_util.run_query(query, (MAP_TYPE, settings.EnumWfsWmsStatus.AVAILABLE.value, ))

    for workspace, publ_type, publication in publications:
        logger.info(f'    Adjust description of {publ_type} {workspace}.{publication}')
        try:
            if publ_type == LAYER_TYPE:
                wms = get_wms_proxy(f'{workspace}_wms')
                description = wms.contents[publication].abstract
            else:
                description = input_file.get_map_info(workspace, publication)['description']
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.HTTPError):
            description = None

        query = f'''update {DB_SCHEMA}.publications set
        description = %s
        where type = %s
          and name = %s
          and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
        params = (description, publ_type, publication, workspace,)
        db_util.run_statement(query, params)

    logger.info(f'    Adjusting publications description DONE')
