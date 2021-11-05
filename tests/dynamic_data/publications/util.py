import itertools


def dictionary_product(source):
    names = list(source.keys())
    all_values = [list(source[p_name].keys()) for p_name in names]
    values = itertools.product(*all_values)
    param_dict = [{names[idx]: value for idx, value in enumerate(vals)} for vals in values]
    return param_dict
