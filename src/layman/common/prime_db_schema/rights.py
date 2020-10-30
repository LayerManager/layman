import logging

from . import util
from layman import settings

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
logger = logging.getLogger(__name__)


def insert_rights(id_publication,
                  users,
                  type,
                  ):
    insert_sql = f'''insert into {DB_SCHEMA}.rights (id_user, id_publication, type)
        select u.id,
               %s,
               %s
        from {DB_SCHEMA}.users u inner join
             {DB_SCHEMA}.workspaces w on w.id = u.id_workspace
        where w.name = %s
returning id
;'''
    for username in users:
        util.run_query(insert_sql, (id_publication,
                                    type,
                                    username,
                                    ))


def delete_rights(id_publication):
    delete_sql = f'''delete from {DB_SCHEMA}.rights where id_publication = %s;'''
    util.run_statement(delete_sql,
                       (id_publication,)
                       )
