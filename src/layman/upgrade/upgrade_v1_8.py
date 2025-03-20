import logging

from layman import app, settings
from layman.common.prime_db_schema import schema_initialization

logger = logging.getLogger(__name__)


def upgrade_1_8():
    logger.info(f'Upgrade to version 1.8.x')
    with app.app_context():
        logger.info(f'  Creating prime_db_schema')
        schema_initialization.ensure_schema(settings.LAYMAN_PRIME_SCHEMA)
