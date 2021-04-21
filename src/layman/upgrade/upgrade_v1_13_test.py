import os
import logging
import pathlib

from layman import settings
from . import upgrade_v1_13
logger = logging.getLogger(__name__)


def test_rename_users_directory():
    old_name = os.path.join(settings.LAYMAN_DATA_DIR, 'users')
    new_name = os.path.join(settings.LAYMAN_DATA_DIR, 'workspaces')
    assert not os.path.exists(old_name)
    if os.path.exists(new_name):
        os.rename(new_name, old_name)
    else:
        pathlib.Path(old_name).mkdir(parents=True, exist_ok=True)
    upgrade_v1_13.rename_users_directory()

    assert os.path.exists(new_name)
