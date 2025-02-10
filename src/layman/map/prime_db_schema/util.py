from db import util as db_util
from layman import settings
from layman.util import get_publication_info
from .. import MAP_TYPE

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def ensure_internal_layers(workspace, mapname, layers):
    map_info = get_publication_info(workspace, MAP_TYPE, mapname, context={'keys': ['id', 'map_layers'], })
    map_id = map_info['id']
    db_layers = {(layer_dict['uuid'], layer_dict['index'], ) for layer_dict in map_info['_map_layers']}

    to_insert = set(layers) - db_layers
    to_delete = db_layers - set(layers)

    for layer_uuid, layer_index in to_insert:
        insert_query = f'''
        insert into {DB_SCHEMA}.map_layer(id_map, layer_uuid, layer_index) values (%s, %s, %s);
        '''
        db_util.run_statement(insert_query, (map_id, layer_uuid, layer_index,))

    for layer_uuid, layer_index in to_delete:
        delete_query = f'''
        delete from {DB_SCHEMA}.map_layer
        where id_map = %s
          and layer_uuid = %s
          and layer_index = %s
          ;
        '''
        db_util.run_statement(delete_query, (map_id, layer_uuid, layer_index,))


def delete_internal_layer_relations(workspace, mapname):
    map_id = get_publication_info(workspace, MAP_TYPE, mapname, context={'keys': ['id'], })['id']

    delete_query = f'''
    delete from {DB_SCHEMA}.map_layer where id_map = %s;
    '''
    db_util.run_statement(delete_query, (map_id, ))
