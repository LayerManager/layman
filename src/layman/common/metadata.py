import json
from layman.util import get_publication_types

PUBL_TYPE_DEF_KEY = __name__


def get_syncable_prop_names(publ_type):
    publ_types = get_publication_types()
    prop_names = publ_types[publ_type][PUBL_TYPE_DEF_KEY]['syncable_properties']
    return prop_names


def extent_equals(a, b, limit=0.95):
    isect = _get_extent_intersetion(a, b)
    if _is_extent_empty(isect):
        return False

    a_area = _get_extent_area(a)
    b_area = _get_extent_area(b)
    i_area = _get_extent_area(isect)

    similarity = i_area / a_area * i_area / b_area
    # current_app.logger.info(f"a={a}, b={b}, similarity={similarity}")
    return similarity >= limit


PROPERTIES = {
    'md_file_identifier': {
        'upper_mp': '1',
    },
    'md_language': {
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
    'revision_date': {
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
        'upper_mp': '*',
        'lower_mp': '1',
        'equals_fn': lambda a, b: set(a) == set(b),
        'empty_fn': lambda a: isinstance(a, list) and len(a) == 0,
    },
    'extent': {
        'upper_mp': '1',
        'equals_fn': extent_equals,
    },
    'wms_url': {
        'upper_mp': '1',
        'equals_fn': lambda a, b: strip_capabilities_params(a) == strip_capabilities_params(b),
    },
    'wfs_url': {
        'upper_mp': '1',
        'equals_fn': lambda a, b: strip_capabilities_params(a) == strip_capabilities_params(b),
    },
    'layer_endpoint': {
        'upper_mp': '1',
    },
    'operates_on': {
        'upper_mp': '*',
        'equals_fn': lambda a, b: set(json.dumps(ai, sort_keys=True) for ai in a) == set(
            json.dumps(bi, sort_keys=True) for bi in b),
    },
    'map_endpoint': {
        'upper_mp': '1',
    },
    'map_file_endpoint': {
        'upper_mp': '1',
    },
}


def prop_equals(value_a, value_b, equals_fn=None):
    equals_fn = equals_fn or (lambda a, b: a == b)
    if value_a is None or value_b is None:
        return value_a is value_b
    return equals_fn(value_a, value_b)


def prop_equals_or_none(values, equals_fn=None):
    equals_fn = equals_fn or (lambda a, b: a == b)
    values = [v for v in values if v is not None]
    return prop_equals_strict(values, equals_fn)


def prop_equals_or_empty(values, equals_fn=None, empty_fn=None):
    equals_fn = equals_fn or (lambda a, b: a == b)
    empty_fn = empty_fn or (lambda a: False)
    values = [
        v for v in values
        if not (v is None or empty_fn(v))
    ]
    return prop_equals_strict(values, equals_fn)


def prop_equals_strict(values, equals_fn=None):
    equals_fn = equals_fn or (lambda a, b: a == b)
    if len(values) < 2:
        return True
    result = True
    for idx in range(len(values) - 1):
        v1 = values[idx]
        v2 = values[idx + 1]
        result = v1 is v2 if (v1 is None or v2 is None) else equals_fn(v1, v2)
        if not result:
            break
    return result


def strip_capabilities_params(url):
    from layman.layer.geoserver.wms import strip_params_from_url
    return strip_params_from_url(url, ['SERVICE', 'REQUEST', 'VERSION'])


def _is_extent_empty(e):
    return any((c is None for c in e))


def _get_extent_area(e):
    return (e[2] - e[0]) * (e[3] - e[1])


def _get_extent_intersetion(a, b):
    intersection = [None] * 4
    if _extent_intersects(a, b):
        if a[0] > b[0]:
            intersection[0] = a[0]
        else:
            intersection[0] = b[0]
        if a[1] > b[1]:
            intersection[1] = a[1]
        else:
            intersection[1] = b[1]
        if a[2] < b[2]:
            intersection[2] = a[2]
        else:
            intersection[2] = b[2]
        if a[3] < b[3]:
            intersection[3] = a[3]
        else:
            intersection[3] = b[3]
    return intersection


def _extent_intersects(a, b):
    return a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]


def transform_metadata_props_to_comparison(all_props):
    prop_names = sorted(list(set(pn for po in all_props.values() for pn in po.keys())))
    sources = {
        f"s{idx + 1}": {
            'url': k
        }
        for idx, k in enumerate(sorted(list(all_props.keys())))
    }
    src_url_to_idx = {}
    for k, v in sources.items():
        src_url_to_idx[v['url']] = k
    all_props = {
        'metadata_sources': sources,
        'metadata_properties': {
            pn: {
                'values': {
                    f"{src_url_to_idx[src]}": prop_object[pn]
                    for src, prop_object in all_props.items()
                    if pn in prop_object
                },
            }
            for pn in prop_names
        }
    }
    for pn, po in all_props['metadata_properties'].items():
        equals_fn = PROPERTIES[pn].get('equals_fn', None)
        po['equal_or_null'] = prop_equals_or_none(po['values'].values(), equals_fn=equals_fn)
        po['equal'] = prop_equals_strict(list(po['values'].values()), equals_fn=equals_fn)
    return all_props


def get_same_or_missing_prop_names(prop_names, comparison):
    prop_names = [
        pn for pn in prop_names
        if (pn in comparison['metadata_properties'] and comparison['metadata_properties'][pn]['equal']) or (
            pn not in comparison['metadata_properties'])
    ]
    # current_app.logger.info(f'prop_names after filtering: {prop_names}')
    return prop_names


def is_empty(v, prop_name):
    return v is None or PROPERTIES[prop_name].get('empty_fn', lambda _: False)(v)
