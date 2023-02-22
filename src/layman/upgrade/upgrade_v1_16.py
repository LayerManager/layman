import json
import logging
from jsonschema import validate, Draft7Validator
import requests

from crs import EPSG_3857
from db import util as db_util
from layman import settings
from layman.common import bbox as bbox_util
from layman.common.prime_db_schema import publications as db_publications
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE, util as map_util
from layman.map.filesystem import input_file

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

JSON_EXTENT_CRS = 'EPSG:4326'


def adjust_db_for_srid():
    logger.info(f'    Alter DB prime schema for native EPSG')

    statement = f'ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS srid integer;'
    db_util.run_statement(statement)


def adjust_db_publication_layer_srid_data():
    crs = EPSG_3857
    srid = db_util.get_internal_srid(crs)

    statement = f'''
    update {DB_SCHEMA}.publications set
      srid = %s
    where srid is null
      and type = %s
    ;'''
    db_util.run_statement(statement, (srid, LAYER_TYPE))


def adjust_maps():
    logger.info(f'    Adjust maps')
    query = f'''select w.name,
        p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
    ;'''
    publications = db_util.run_query(query, (MAP_TYPE, ))

    schema_url = 'https://raw.githubusercontent.com/hslayers/map-compositions/2.0.0/schema.json'
    res = requests.get(schema_url,
                       timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    res.raise_for_status()
    schema_txt = res.text
    schema_json = json.loads(schema_txt)

    for workspace, publication in publications:
        logger.info(f'      Adjusting {workspace}.{publication}')
        map_file_path = input_file.get_map_file(workspace, publication)
        mapjson = map_util.get_map_file_json(workspace, publication)
        bbox_json = map_util.get_bbox_from_json(mapjson)
        crs = map_util.get_crs_from_json(mapjson)
        assert crs in settings.INPUT_SRS_LIST
        bbox = bbox_util.transform(bbox_json, JSON_EXTENT_CRS, crs)
        db_publications.set_bbox(workspace, MAP_TYPE, publication, bbox, crs, )

        mapjson['describedBy'] = "https://raw.githubusercontent.com/hslayers/map-compositions/2.0.0/schema.json"
        mapjson['schema_version'] = "2.0.0"
        mapjson['extent'] = list(bbox_json)
        mapjson['nativeExtent'] = list(bbox)

        validator = Draft7Validator(schema_json)
        assert validator.is_valid(mapjson), [
            {
                'message': e.message,
                'absolute_path': list(e.absolute_path),
            }
            for e in validator.iter_errors(mapjson)
        ]
        validate(instance=mapjson, schema=schema_json)

        with open(map_file_path, 'w') as file:
            json.dump(mapjson, file, indent=2)
    logger.info(f'    Adjusting maps DONE')


def adjust_db_publication_srid_constraint():
    statement = f'alter table {DB_SCHEMA}.publications add constraint bbox_with_crs_check CHECK ' \
                f'(bbox is null or srid is not null);'
    db_util.run_statement(statement)


def ensure_gs_users():
    from layman.layer import geoserver
    from .. import util as layman_util

    for username in layman_util.get_usernames():
        geoserver.ensure_whole_user(username)
