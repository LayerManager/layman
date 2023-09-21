import logging

from db import util as db_util
from layman import settings
from layman.http import LaymanError
from layman.util import get_workspaces as global_get_workspaces
from . import model

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ROLE_EVERYONE = settings.RIGHTS_EVERYONE_ROLE

logger = logging.getLogger(__name__)


def schema_exists():
    return db_util.run_query(model.EXISTS_SCHEMA_SQL)[0][0] > 0


def ensure_schema(db_schema):
    if not schema_exists():
        try:
            db_util.run_statement(model.CREATE_SCHEMA_SQL)
            db_util.run_statement(model.setup_codelists_data())
        except BaseException as exc:
            db_util.run_statement(model.DROP_SCHEMA_SQL, )
            raise exc
    else:
        logger.info(f"Layman DB schema already exists, schema_name={db_schema}")


def check_schema_name(db_schema):
    usernames = global_get_workspaces(use_cache=False, skip_modules=('layman.map.prime_db_schema', 'layman.layer.prime_db_schema',))
    if db_schema in usernames:
        raise LaymanError(42, {'workspace': db_schema})
