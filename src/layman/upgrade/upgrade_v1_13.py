import os
import logging

from layman import settings
logger = logging.getLogger(__name__)


def rename_users_directory():
    logger.info(f'    Starting - Rename directory users to workspaces')
    old_name = os.path.join(settings.LAYMAN_DATA_DIR, 'users')
    new_name = os.path.join(settings.LAYMAN_DATA_DIR, 'workspaces')
    if os.path.exists(old_name):
        os.rename(old_name, new_name)
    logger.info(f'    DONE - Rename directory users to workspaces')
