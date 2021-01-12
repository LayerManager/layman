import logging
import os

from layman.http import LaymanError
from layman.authn.filesystem import get_authn_info
from layman.common.prime_db_schema import workspaces, users, publications as publications_module
from layman.util import get_usernames as global_get_workspaces
from layman import util as layman_util
from . import util as db_util, model
from ...layer.filesystem import util as fs_layer_util
from ...map.filesystem import util as fs_map_util
from ...map.filesystem.input_file import get_map_info
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE

logger = logging.getLogger(__name__)


def migrate_users_and_publications(role_everyone):
    workspace_names = global_get_workspaces(use_cache=False)

    for workspace_name in workspace_names:
        userinfo = get_authn_info(workspace_name)
        id_workspace = workspaces.ensure_workspace(workspace_name)
        if userinfo:
            # It is personal workspace
            iss_sub_infos = users.get_user_infos(iss_sub={'issuer_id': userinfo["iss_id"],
                                                          'sub': userinfo["sub"]})
            if iss_sub_infos:
                username_in_conflict, iss_sub_info = iss_sub_infos.popitem()
                raise LaymanError(f"Two workspaces are registered as private workspaces of the same user. To migrate successfully, "
                                  f"choose which workspace should be the only private workspace of the user, delete authn.txt file "
                                  f"from the other workspace, and restart layman. The other workspace becomes public.",
                                  data={'user': iss_sub_info,
                                        'workspaces': [workspace_name, username_in_conflict]
                                        }
                                  )
            userinfo['issuer_id'] = userinfo['iss_id']
            users.ensure_user(id_workspace, userinfo)
            roles = {workspace_name, }
        else:
            # It is public workspace, so all publications are available to everybody
            roles = {role_everyone, }

        for (publ_type, infos_method) in [(LAYER_TYPE, get_layer_infos),
                                          (MAP_TYPE, get_map_infos)
                                          ]:
            publications = infos_method(workspace_name)
            for name in publications:
                info = layman_util.get_publication_info(workspace_name, publ_type, name)
                pub_info = {"name": name,
                            "title": info.get("title", name),
                            "publ_type_name": publ_type,
                            "uuid": info["uuid"],
                            "actor_name": workspace_name,
                            "access_rights": {"read": {role_everyone, },
                                              "write": roles,
                                              }
                            }
                publications_module.insert_publication(workspace_name, pub_info)


def schema_exists():
    return db_util.run_query(model.EXISTS_SCHEMA_SQL)[0][0] > 0


def ensure_schema(db_schema,
                  role_everyone):
    if not schema_exists():
        try:
            db_util.run_statement(model.CREATE_SCHEMA_SQL)
            db_util.run_statement(model.setup_codelists_data())
            migrate_users_and_publications(role_everyone)
        except BaseException as exc:
            db_util.run_statement(model.DROP_SCHEMA_SQL, conn_cur=db_util.create_connection_cursor())
            raise exc
    else:
        logger.info(f"Layman DB schema already exists, schema_name={db_schema}")


def check_schema_name(db_schema):
    usernames = global_get_workspaces(use_cache=False, skip_modules=('layman.map.prime_db_schema', 'layman.layer.prime_db_schema',))
    if db_schema in usernames:
        raise LaymanError(42, {'workspace': db_schema})


def get_layer_infos(username):
    layersdir = fs_layer_util.get_layers_dir(username)
    layer_infos = {}
    if os.path.exists(layersdir):
        layer_infos = {subfile: {"name": subfile}
                       for subfile in os.listdir(layersdir) if os.path.isdir(os.path.join(layersdir, subfile))}
    return layer_infos


def get_map_infos(username):
    mapsdir = fs_map_util.get_maps_dir(username)
    map_infos = {}
    if os.path.exists(mapsdir):
        for name in os.listdir(mapsdir):
            info = get_map_info(username, name)
            map_infos[name] = {"name": name,
                               "title": info["title"]}
    return map_infos
