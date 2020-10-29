import logging

from layman.http import LaymanError
from layman.authn.filesystem import get_authn_info
from layman.common.prime_db_schema import workspaces, users, publications
from layman.common.util import merge_infos
from layman.util import get_modules_from_names, call_modules_fn, get_usernames as global_get_workspaces
from . import util as db_util, model

logger = logging.getLogger(__name__)


def migrate_users_and_publications(modules, role_everyone):
    workspace_names = global_get_workspaces(use_cache=False)

    for workspace_name in workspace_names:
        userinfo = get_authn_info(workspace_name)
        id_workspace = workspaces.ensure_workspace(workspace_name)
        if userinfo:
            # It is personal workspace
            users.ensure_user(id_workspace, userinfo)
            roles = {workspace_name, }
        else:
            # It is public workspace, so all publications are available to everybody
            roles = {role_everyone, }
        for publ_module in get_modules_from_names(modules):
            for type_def in publ_module.PUBLICATION_TYPES.values():
                publ_type_name = type_def['type']
                sources = get_modules_from_names(type_def['internal_sources'])
                results = call_modules_fn(sources, 'get_publication_infos', [workspace_name, publ_type_name])
                pubs = merge_infos(results)
                for name, info in pubs.items():
                    pub_info = {"name": name,
                                "title": info.get("title"),
                                "publ_type_name": publ_type_name,
                                "uuid": info["uuid"],
                                "can_read": roles,
                                "can_write": roles,
                                }
                    publications.insert_publication(workspace_name, pub_info)


def ensure_schema(db_schema,
                  modules,
                  role_everyone):
    exists_schema = db_util.run_query(model.EXISTS_SCHEMA_SQL)
    if exists_schema[0][0] == 0:
        db_util.run_statement(model.CREATE_SCHEMA_SQL)
        db_util.run_statement(model.setup_codelists_data())
        migrate_users_and_publications(modules, role_everyone)
    else:
        logger.info(f"Layman DB schema already exists, schema_name={db_schema}")


def check_schema_name(db_schema):
    usernames = global_get_workspaces(use_cache=False, skip_modules=('layman.map.prime_db_schema', 'layman.layer.prime_db_schema',))
    if db_schema in usernames:
        raise LaymanError(42, {'username': db_schema})
