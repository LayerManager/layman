import os
import pathlib
import shutil

from layman import settings
from layman.util import get_publication_types

PUBL_TYPE_DEF_KEY = '.'.join(__name__.split('.')[:-1])


def get_usernames():
    return []


def get_publications_dir(publ_type):
    publ_types = get_publication_types()
    dirname = publ_types[publ_type][PUBL_TYPE_DEF_KEY]['publications_dir']
    layersdir = os.path.join(settings.LAYMAN_DATA_DIR, dirname)
    return layersdir


def get_publication_dir(publ_type, publ_uuid):
    publ_dir = os.path.join(
        get_publications_dir(publ_type),
        publ_uuid,
    )
    return publ_dir


def ensure_publication_dir(publ_type, publ_uuid):
    publ_dir = get_publication_dir(publ_type, publ_uuid)
    pathlib.Path(publ_dir).mkdir(exist_ok=True, parents=True)
    return publ_dir


def delete_publication_subfile(publ_type, publ_uuid, subfile):
    publ_dir = get_publication_dir(publ_type, publ_uuid)
    publ_subfile = os.path.join(publ_dir, subfile)
    try:
        os.remove(publ_subfile)
    except OSError:
        pass
    if os.path.exists(publ_dir) and not os.listdir(publ_dir):
        os.rmdir(publ_dir)
    return {}


def delete_publication_subdir(publ_type, publ_uuid, subdir):
    publ_dir = get_publication_dir(publ_type, publ_uuid)
    publ_subdir = os.path.join(publ_dir, subdir)
    try:
        shutil.rmtree(publ_subdir)
    except FileNotFoundError:
        pass
    if os.path.exists(publ_dir) and not os.listdir(publ_dir):
        os.rmdir(publ_dir)
    return {}
