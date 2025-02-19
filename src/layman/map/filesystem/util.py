from functools import partial

from layman.common.filesystem import util as publ_util

MAP_TYPE = '.'.join(__name__.split('.')[:-2])

# workspace, mapname
get_map_dir = partial(publ_util.get_publication_dir, MAP_TYPE)

# workspace, mapname, subdir
delete_map_subdir = partial(publ_util.delete_publication_subdir, MAP_TYPE)
