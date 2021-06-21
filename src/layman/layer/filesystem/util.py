from functools import partial
from layman.common.filesystem import util as publ_util

LAYER_TYPE = '.'.join(__name__.split('.')[:-2])

# username
get_layers_dir = partial(publ_util.get_publications_dir, LAYER_TYPE)

# username, layername
get_layer_dir = partial(publ_util.get_publication_dir, LAYER_TYPE)

# username, layername
ensure_layer_dir = partial(publ_util.ensure_publication_dir, LAYER_TYPE)

# username, layername, subdir
delete_layer_subdir = partial(publ_util.delete_publication_subdir, LAYER_TYPE)
