from dataclasses import dataclass
import os
from zipfile import ZipFile
from functools import partial
from werkzeug.datastructures import FileStorage

from layman import settings
from layman.common.filesystem import util as publ_util

LAYER_TYPE = '.'.join(__name__.split('.')[:-2])

# workspace, layername
get_layer_dir = partial(publ_util.get_publication_dir, LAYER_TYPE)

# workspace, layername, subdir
delete_layer_subdir = partial(publ_util.delete_publication_subdir, LAYER_TYPE)


@dataclass(frozen=True)
class InputFiles:
    def __init__(self, *, sent_streams=None, sent_paths=None, saved_paths=None):
        sent_streams = sent_streams or []
        sent_paths = sent_paths or []
        saved_paths = saved_paths or []
        assert sum((len(lst) > 0 for lst in [sent_streams, sent_paths, saved_paths])) <= 1
        object.__setattr__(self, '_sent_streams', sent_streams)
        object.__setattr__(self, '_sent_paths', sent_paths)
        object.__setattr__(self, '_saved_paths', saved_paths)

    def __bool__(self):
        return bool(self.raw_paths)

    @property
    def sent_streams(self):
        # pylint: disable=no-member
        return self._sent_streams

    @property
    def sent_paths(self):
        # pylint: disable=no-member
        return self._sent_paths

    @property
    def saved_paths(self):
        # pylint: disable=no-member
        return self._saved_paths

    @property
    def raw_paths(self):
        return [f.filename for f in self.sent_streams] + self.sent_paths + self.saved_paths

    @property
    def raw_paths_to_archives(self):
        return [fp for fp in self.raw_paths if os.path.splitext(fp)[1].lower() in settings.COMPRESSED_FILE_EXTENSIONS]

    @property
    def archive_streams(self):
        return [fs for fs in self.sent_streams
                if os.path.splitext(fs.filename)[1].lower() in settings.COMPRESSED_FILE_EXTENSIONS]

    @property
    def saved_paths_to_archives(self):
        return [fp for fp in self.saved_paths
                if os.path.splitext(fp)[1].lower() in settings.COMPRESSED_FILE_EXTENSIONS]

    @property
    def is_one_archive(self):
        return len(self.raw_paths_to_archives) == 1 and not self.raw_main_file_paths

    @property
    def is_one_archive_with_available_content(self):
        return self.is_one_archive and (self.archive_streams or self.saved_paths_to_archives)

    def archived_paths(self, *, with_zip_in_path=False):
        return [
            path_to_archived_file
            for archives in self.archive_streams + self.saved_paths_to_archives
            for path_to_archived_file in get_filenames_from_zip_storage(archives,
                                                                        with_zip_in_path=with_zip_in_path)
        ]

    @property
    def raw_or_archived_paths(self):
        if self.is_one_archive_with_available_content:
            return self.archived_paths(with_zip_in_path=True) or self.raw_paths
        return self.raw_paths

    @property
    def raw_main_file_paths(self):
        result = sorted([fn for fn in self.raw_paths
                         if os.path.splitext(fn)[1].lower() in get_all_allowed_main_extensions()])
        return result

    @property
    def archived_main_file_paths(self):
        result = sorted([fn for fn in self.archived_paths(with_zip_in_path=True)
                         if os.path.splitext(fn)[1].lower() in get_all_allowed_main_extensions()])
        return result

    @property
    def raw_or_archived_main_file_paths(self):
        result = sorted([fn for fn in self.raw_or_archived_paths
                         if os.path.splitext(fn)[1].lower() in get_all_allowed_main_extensions()])
        return result

    @property
    def raw_or_archived_main_file_path(self):
        paths = self.raw_or_archived_main_file_paths
        if len(paths) >= 1:
            return paths[0]
        return None

    @property
    def archive_type(self):
        return os.path.splitext(self.saved_paths_to_archives[0])[1].lower() if self.is_one_archive else None

    @property
    def saved_paths_dir(self):
        result = None
        if self.saved_paths:
            first_dir = os.path.split(self.saved_paths[0])[0]
            assert all(os.path.split(fp)[0] == first_dir for fp in self.saved_paths)
            result = first_dir
        return result


def get_filenames_from_zip_storage(zip_file, *, with_zip_in_path=False):
    with ZipFile(zip_file) as opened_zip_file:
        filenames = opened_zip_file.namelist()
    if isinstance(zip_file, FileStorage):
        zip_file.seek(0)
        zip_name = zip_file.filename
    else:
        zip_name = zip_file
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


def get_all_allowed_main_extensions():
    result = list(settings.MAIN_FILE_EXTENSIONS.keys())
    return result
