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
    for key in ['id', 'type', 'style_type']:
        try:
            del info[key]
        except KeyError:
            pass
    info['updated_at'] = info['updated_at'].isoformat()
    return info


def bbox_is_empty(bbox):
    return all(num is None for num in bbox)
