import json

PROPERTIES = {
    'md_file_identifier': {
        'upper_mp': '1',
    },
    'md_organisation_name': {
        'upper_mp': '1',
    },
    'md_date_stamp': {
        'upper_mp': '1',
    },
    'reference_system': {
        'upper_mp': '*',
        'equals_fn': lambda a, b: set(a) == set(b),
    },
    'title': {
        'upper_mp': '1',
    },
    'publication_date': {
        'upper_mp': '1',
    },
    'identifier': {
        'upper_mp': '1',
    },
    'abstract': {
        'upper_mp': '1',
    },
    'organisation_name': {
        'upper_mp': '1',
    },
    'graphic_url': {
        'upper_mp': '1',
    },
    'scale_denominator': {
        'upper_mp': '1',
    },
    'language': {
        'upper_mp': '1',
    },
    'extent': {
        'upper_mp': '1',
    },
    'wms_url': {
        'upper_mp': '1',
    },
    'wfs_url': {
        'upper_mp': '1',
    },
    'layer_endpoint': {
        'upper_mp': '1',
    },
    'operates_on': {
        'upper_mp': '*',
        'equals_fn': lambda a, b: set([json.dumps(ai, sort_keys=True) for ai in a]) == set([json.dumps(bi, sort_keys=True) for bi in b]),
    },
    'map_endpoint': {
        'upper_mp': '1',
    },
    'map_file_endpoint': {
        'upper_mp': '1',
    },
}


def prop_equals(value_a, value_b, equals_fn=None):
    equals_fn = equals_fn or (lambda a,b: a==b)
    if value_a is None or value_b is None:
        return value_a is value_b
    else:
        return equals_fn(value_a, value_b)


def prop_equals_or_none(values, equals_fn=None):
    equals_fn = equals_fn or (lambda a,b: a==b)
    values = [v for v in values if v is not None]
    if len(values)<2:
        return True
    result = True
    for idx in range(len(values)-1):
        result = equals_fn(values[idx], values[idx+1])
        if not result:
            break
    return result
