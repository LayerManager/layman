from collections import defaultdict


PUBLICATION_NAME_ONLY_PATTERN = r"[a-z0-9]*(?:_[a-z0-9]+)*"
PUBLICATION_NAME_PATTERN = r"^" + PUBLICATION_NAME_ONLY_PATTERN + r"$"
PUBLICATION_MAX_LENGTH = 210  # File-system limitation


def merge_infos(infos):
    result_infos = defaultdict(dict)
    for source in infos:
        for (name, info) in source.items():
            result_infos[name].update(info)
    return result_infos


def clear_publication_info(info):
    clear_info = {key: value for key, value in info.items() if not (key.startswith('_') or key in ['id', 'type', 'style_type', ])}
    clear_info['updated_at'] = clear_info['updated_at'].isoformat()
    return clear_info
