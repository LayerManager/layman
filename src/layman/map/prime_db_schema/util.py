from db import util as db_util
from layman import settings
from layman.util import get_publication_info
from .. import MAP_TYPE

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def insert_internal_layers(workspace, mapname, layers):
    map_id = get_publication_info(workspace, MAP_TYPE, mapname, context={'keys': ['id'], })['id']
    for layer_workspace, layer_name, layer_index in layers:
        insert_query = f'''
        insert into {DB_SCHEMA}.map_layer(id_map, layer_workspace, layer_name, layer_index) values (%s, %s, %s, %s);
        '''
        db_util.run_statement(insert_query, (map_id, layer_workspace, layer_name, layer_index,))


def delete_internal_layer_relations(workspace, mapname):
    map_id = get_publication_info(workspace, MAP_TYPE, mapname, context={'keys': ['id'], })['id']

    delete_query = f'''
    delete from {DB_SCHEMA}.map_layer where id_map = %s;
    '''
    db_util.run_statement(delete_query, (map_id, ))
