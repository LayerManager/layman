from layman.db.utils import run_query, run_statement
from layman.util import get_usernames, get_modules_from_names, call_modules_fn
from layman.common.util import merge_infos
from layman import settings, app
from layman.authz.util import get_publication_access_rights
from layman.db import model


DB_SCHEMA = settings.PG_LAYMAN_SCHEMA


def migrate_users_with_publications():
    everyone_can_read = model.BOOLEAN_TRUE
    everyone_can_write = get_publication_access_rights('', '', '')["guest"] == "w"
    insert_users_sql = f'''insert into {DB_SCHEMA}.users (username) values (%s) returning ID;'''

    insert_publications_sql = f'''insert into {DB_SCHEMA}.publications
    (id_user, name, title, type, uuid, everyone_can_read, everyone_can_write) values
    (%s, %s, %s, %s, %s, %s, %s);'''

    usernames = get_usernames(use_cache=False)

    for username in usernames:
        user_id = run_query(insert_users_sql, (username, ))[0][0]
        for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
            for type_def in publ_module.PUBLICATION_TYPES.values():
                publ_type_name = type_def['type']
                sources = get_modules_from_names(type_def['internal_sources'])
                results = call_modules_fn(sources, 'get_publication_infos', [username, publ_type_name])
                publications = merge_infos(results)
                for name, info in publications.items():
                    run_statement(insert_publications_sql, (user_id,
                                                            name,
                                                            info.get("title"),
                                                            publ_type_name,
                                                            info.get("uuid"),
                                                            everyone_can_read,
                                                            everyone_can_write,))


def ensure_schema():
    exists_schema = run_query(model.EXISTS_SCHEMA_SQL)
    if exists_schema[0][0] == 0:
        app.logger.info(f"Going to create Layman DB schema, schema_name={DB_SCHEMA}")
        run_statement(model.CREATE_SCHEMA_SQL)
        run_statement(model.setup_codelists_data())
        migrate_users_with_publications()
    else:
        app.logger.info(f"Layman DB schema already exists, schema_name={DB_SCHEMA}")
