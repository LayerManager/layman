import os
import pathlib
import shutil
from functools import partial
from dataclasses import dataclass

from layman import settings
from layman.common import empty_method
from layman.util import get_publication_types
from layman.layer import LAYER_TYPE

PUBL_TYPE_DEF_KEY = __name__

check_workspace_name = empty_method
ensure_whole_user = empty_method
delete_whole_user = empty_method
ensure_workspace = empty_method
delete_workspace = empty_method


@dataclass(frozen=True)
class QgisNames:
    id: str  # pylint: disable=invalid-name
    name: str

    def __init__(self, *, uuid: str):
        object.__setattr__(self, 'id', f'l_{uuid}')
        object.__setattr__(self, 'name', f'l_{uuid}')


def get_usernames():
    return []


def get_workspaces():
    return []


def get_publications_dir(publ_type):
    publ_types = get_publication_types()
    dirname = publ_types[publ_type][PUBL_TYPE_DEF_KEY]['publications_dir']
    layersdir = os.path.join(settings.LAYMAN_QGIS_DATA_DIR, dirname)
    return layersdir


def get_publication_dir(publ_type, publ_uuid):
    publ_dir = os.path.join(
        get_publications_dir(publ_type),
        publ_uuid
    )
    return publ_dir


def ensure_publication_dir(publ_type, publ_uuid):
    publ_dir = get_publication_dir(publ_type, publ_uuid)
    pathlib.Path(publ_dir).mkdir(exist_ok=True, parents=True)
    return publ_dir


def delete_publication_dir(publ_type, publ_uuid):
    publ_dir = get_publication_dir(publ_type, publ_uuid)
    try:
        shutil.rmtree(publ_dir)
    except FileNotFoundError:
        pass
    if os.path.exists(publ_dir) and not os.listdir(publ_dir):
        os.rmdir(publ_dir)
    return {}


get_layer_dir = partial(get_publication_dir, LAYER_TYPE)

ensure_layer_dir = partial(ensure_publication_dir, LAYER_TYPE)

delete_layer_dir = partial(delete_publication_dir, LAYER_TYPE)
