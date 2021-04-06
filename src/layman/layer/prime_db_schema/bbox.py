from layman import patch_mode, settings
from layman.common.prime_db_schema import util as db_util

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def get_publication_uuid(username, publication_type, publication_name):
    return None


def get_layer_info(username, layername):
    return dict()


def delete_layer(username, layer_name):
    pass


def patch_layer(username,
                layername,
                actor_name,
                style_type=None,
                title=None,
                access_rights=None,
                ):
    pass


def pre_publication_action_check(username,
                                 layername,
                                 actor_name,
                                 access_rights=None,
                                 ):
    pass


def post_layer(username,
               layername,
               access_rights,
               title,
               uuid,
               actor_name,
               style_type=None,
               ):
    pass


def get_metadata_comparison(username, publication_name):
    pass


def set_bbox(workspace, layer, bbox):
    query = f'''update {DB_SCHEMA}.publications set
    bbox = ST_MakeBox2D(ST_Point(%s, %s), ST_Point(%s ,%s))
    where name = %s
      and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
    params = bbox + (layer, workspace, )
    db_util.run_statement(query, params)
