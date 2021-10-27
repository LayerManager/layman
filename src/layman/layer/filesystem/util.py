import os
from zipfile import ZipFile
from functools import partial
from werkzeug.datastructures import FileStorage

from layman import settings
from layman.common.filesystem import util as publ_util

LAYER_TYPE = '.'.join(__name__.split('.')[:-2])

# workspace
get_layers_dir = partial(publ_util.get_publications_dir, LAYER_TYPE)

# workspace, layername
get_layer_dir = partial(publ_util.get_publication_dir, LAYER_TYPE)

# workspace, layername
ensure_layer_dir = partial(publ_util.ensure_publication_dir, LAYER_TYPE)

# workspace, layername, subdir
delete_layer_subdir = partial(publ_util.delete_publication_subdir, LAYER_TYPE)


def get_filenames_from_zip_storage(zip_file, *, with_zip_in_path=False):
    with ZipFile(zip_file) as opened_zip_file:
        filenames = opened_zip_file.namelist()
    if isinstance(zip_file, FileStorage):
        zip_file.seek(0)
        zip_name = zip_file.filename
    else:
        zip_name = os.path.basename(zip_file)
    if with_zip_in_path:
        filenames = [os.path.join(zip_name, fn) for fn in filenames]
    return filenames


def get_deepest_real_file(path):
    stripped_path = next((path[len(prefix):] for prefix in settings.COMPRESSED_FILE_EXTENSIONS.values() if path.startswith(prefix)), None)
    if stripped_path:
        path = stripped_path
        while True:
            base_path, _ = os.path.split(path)
            if os.path.exists(base_path):
                result = base_path
                break
            path = base_path
    else:
        result = path
    return result
