import logging
import sys
import time

from db import util as db_util
import geoserver
from geoserver import authn, epsg_properties, role_service
import layman_settings as settings


logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def wait_for_db(conn_dict):
    max_attempts = 60
    attempt = 0

    while True:
        import psycopg2
        try:
            with psycopg2.connect(**conn_dict):
                pass
            logger.info(f"  Attempt {attempt}/{max_attempts} successful.")
            break
        except psycopg2.OperationalError:
            if attempt >= max_attempts:
                logger.info(f"  Reaching max attempts when waiting for DB")
                sys.exit(1)
            time.sleep(2)
            attempt += 1


def ensure_jdbc_role_service_internal_schema():
    db_conn = settings.PG_CONN
    internal_service_schema = settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA
    uri_str = settings.PG_URI_STR

    logger.info(f"Ensuring internal JDBC role service schema. db_conn={db_conn}")

    logger.info(f"  Waiting for DB")
    wait_for_db(db_conn)

    logger.info(f"  Checking internal role service DB schema")
    schema_query = f'''SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = %s;'''
    schema_exists = db_util.run_query(schema_query, (internal_service_schema, ), uri_str=uri_str)[0][0]
    if schema_exists == 0:
        logger.info(f"    Setting up internal role service DB schema")
        statement = f"""
        CREATE SCHEMA "{internal_service_schema}" AUTHORIZATION {settings.LAYMAN_PG_USER};
        create view {internal_service_schema}.roles as select 'ADMIN'::varchar(64) as name, null::varchar(64) as parent
        union all select 'GROUP_ADMIN', null
        union all select %s, null
        ;
        create view {internal_service_schema}.role_props as select null::varchar(64) as rolename, null::varchar(64) as propname, null::varchar(2048) as propvalue;
        create view {internal_service_schema}.user_roles as select %s::varchar(64) as username, 'ADMIN'::varchar(64) as rolename
        union all select %s, %s
        union all select %s, 'ADMIN'
        ;
        create view {internal_service_schema}.group_roles as select null::varchar(128) as groupname, null::varchar(64) as rolename;
    """
        db_util.run_statement(statement, data=(settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_USER, settings.LAYMAN_GS_USER, settings.LAYMAN_GS_ROLE, settings.GEOSERVER_ADMIN_USER, ), uri_str=uri_str)
    else:
        prime_schema_exists = db_util.run_query(schema_query, (settings.LAYMAN_PRIME_SCHEMA, ), uri_str=uri_str)[0][0]
        if prime_schema_exists:
            logger.info(f'  Recreate Role Service admin role views')
            create_admin_roles_view = f"""CREATE OR REPLACE view {internal_service_schema}.admin_roles
            as
            select 'ADMIN' as name
            UNION ALL
            select 'GROUP_ADMIN'
            UNION ALL
            select %s
            ;"""
            db_util.run_statement(create_admin_roles_view, (settings.LAYMAN_GS_ROLE,), uri_str=uri_str)

            create_admin_user_roles_view = f"""CREATE OR REPLACE view {internal_service_schema}.admin_user_roles
            as
            select %s as username, %s as rolename
            UNION ALL
            select %s, 'ADMIN'
            UNION ALL
            select %s, 'ADMIN'
            union all
            select w.name as username,
                   %s as rolename
            from {settings.LAYMAN_PRIME_SCHEMA}.users u inner join
                 {settings.LAYMAN_PRIME_SCHEMA}.workspaces w on w.id = u.id_workspace
            ;"""
            db_util.run_statement(create_admin_user_roles_view, (
                settings.LAYMAN_GS_USER, settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_USER, settings.GEOSERVER_ADMIN_USER,
                settings.LAYMAN_GS_ROLE,), uri_str=uri_str)


def main():
    geoserver.ensure_data_dir(settings.GEOSERVER_DATADIR,
                              settings.GEOSERVER_INITIAL_DATADIR,
                              settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR_NAME)
    authn.setup_authn(settings.GEOSERVER_DATADIR,
                      settings.LAYMAN_GS_AUTHN_FILTER_NAME,
                      settings.LAYMAN_GS_AUTHN_HTTP_HEADER_NAME,
                      settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE,
                      settings.LAYMAN_GS_USER_GROUP_SERVICE,
                      settings.LAYMAN_GS_ROLE_SERVICE,
                      settings.LAYMAN_GS_AUTHN_FILTER_NAME_OLD,
                      )
    ensure_jdbc_role_service_internal_schema()
    role_service.setup_jdbc_role_service(settings.GEOSERVER_DATADIR,
                                         settings.LAYMAN_ROLE_SERVICE_URI,
                                         settings.LAYMAN_GS_ROLE_SERVICE,
                                         settings.LAYMAN_ROLE_SERVICE_SCHEMA,
                                         )
    role_service.set_primary_role_service(settings.GEOSERVER_DATADIR,
                                          settings.LAYMAN_GS_ROLE_SERVICE,
                                          )
    epsg_properties.setup_epsg(settings.GEOSERVER_DATADIR,
                               set(settings.LAYMAN_OUTPUT_SRS_LIST))


if __name__ == "__main__":
    main()
