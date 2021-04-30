from collections import defaultdict
from layman.util import USERNAME_PATTERN, USERNAME_ONLY_PATTERN


PUBLICATION_NAME_ONLY_PATTERN = USERNAME_ONLY_PATTERN
PUBLICATION_NAME_PATTERN = USERNAME_PATTERN


def merge_infos(infos):
    result_infos = defaultdict(dict)
    for source in infos:
        for (name, info) in source.items():
            result_infos[name].update(info)
    return result_infos


def clear_publication_info(info):
    clear_info = {key: value for key, value in info.items() if not (key.startswith('_') or key in ['id', 'type', 'style_type'])}
    clear_info['updated_at'] = clear_info['updated_at'].isoformat()
    return clear_info
