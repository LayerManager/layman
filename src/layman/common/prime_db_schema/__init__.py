from layman.util import get_usernames, get_modules_from_names, call_modules_fn
from layman.common.util import merge_infos
from layman import settings, app, LaymanError
from layman.authz.util import get_publication_access_rights
from layman.authn.filesystem import get_authn_info
from layman.common.prime_db_schema import publications, model, users
from layman.common.prime_db_schema.util import run_query, run_statement


DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def get_default_everyone_can_read():
    return model.BOOLEAN_TRUE


def get_default_everyone_can_write():
    return get_publication_access_rights('', '', '')["guest"] == "w"


def migrate_users_and_publications():
    usernames = get_usernames(use_cache=False)

    for username in usernames:
        userinfo = get_authn_info(username)
        users.ensure_user(username, userinfo)
        for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
            for type_def in publ_module.PUBLICATION_TYPES.values():
                publ_type_name = type_def['type']
                sources = get_modules_from_names(type_def['internal_sources'])
                results = call_modules_fn(sources, 'get_publication_infos', [username, publ_type_name])
                pubs = merge_infos(results)
                for name, info in pubs.items():
                    pub_info = {"name": name,
                                "title": info.get("title"),
                                "publ_type_name": publ_type_name,
                                "uuid": info.get("uuid"),
                                "can_read": set(),
                                "can_write": set(),
                                }
                    publications.insert_publication(username, pub_info)


def check_schema_name():
    usernames = get_usernames(use_cache=False, skip_modules=('layman.map.prime_db_schema', 'layman.layer.prime_db_schema', ))
    if DB_SCHEMA in usernames:
        raise LaymanError(42, {'username': DB_SCHEMA})


def ensure_schema():
    exists_schema = run_query(model.EXISTS_SCHEMA_SQL)
    if exists_schema[0][0] == 0:
        app.logger.info(f"Going to create Layman DB schema, schema_name={DB_SCHEMA}")
        run_statement(model.CREATE_SCHEMA_SQL)
        run_statement(model.setup_codelists_data())
        migrate_users_and_publications()
    else:
        app.logger.info(f"Layman DB schema already exists, schema_name={DB_SCHEMA}")
