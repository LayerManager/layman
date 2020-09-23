def get_names_from_infos(infos):
    return list(set(sorted([info for info in infos])))


def merge_infos(infos):
    result_infos = {}
    # TODO maybe, those two cycles can be done at once
    for source in infos:
        for (name, info) in source.items():
            if result_infos.get(name) is None:
                result_infos[name] = info
            else:
                result_infos[name].update(info)
    return result_infos
