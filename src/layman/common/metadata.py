import json
import crs as crs_def
from layman.common import bbox as bbox_util
from layman.util import get_publication_types

PUBL_TYPE_DEF_KEY = __name__


def get_syncable_prop_names(publ_type):
    publ_types = get_publication_types()
    prop_names = publ_types[publ_type][PUBL_TYPE_DEF_KEY]['syncable_properties']
    return prop_names


def extent_4326_equals(ext1, ext2):
    return bbox_util.are_similar(ext1, ext2, no_area_bbox_padding=crs_def.CRSDefinitions[crs_def.EPSG_4326].no_area_bbox_padding, limit=0.95)


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
    'spatial_resolution': {
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
        'equals_fn': extent_4326_equals,
    },
    'temporal_extent': {
        'upper_mp': '*',
        'equals_fn': lambda a, b: set(a) == set(b),
        'empty_fn': lambda a: isinstance(a, list) and len(a) == 0,
        'ensure_order': True,
        'empty_list_to_none': True,
    },
    'wms_url': {
        'upper_mp': '1',
        'equals_fn': lambda a, b: strip_capabilities_and_layers_params(a) == strip_capabilities_and_layers_params(b),
    },
    'wfs_url': {
        'upper_mp': '1',
        'equals_fn': lambda a, b: strip_capabilities_and_layers_params(a) == strip_capabilities_and_layers_params(b),
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
assert all(prop_val.get('ensure_order') is None or prop_val['upper_mp'] == '*' for prop_val in PROPERTIES.values())


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
        val1 = values[idx]
        val2 = values[idx + 1]
        result = val1 is val2 if (val1 is None or val2 is None) else equals_fn(val1, val2)
        if not result:
            break
    return result


def strip_capabilities_and_layers_params(url):
    from layman.layer.geoserver.wms import strip_params_from_url
    return strip_params_from_url(url, ['SERVICE', 'REQUEST', 'VERSION', 'LAYERS'])


def transform_metadata_props_to_comparison(all_props):
    prop_names = sorted(list(set(pn for po in all_props.values() for pn in po.keys())))
    sources = {
        f"s{idx + 1}": {
            'url': k
        }
        for idx, k in enumerate(sorted(list(all_props.keys())))
    }
    src_url_to_idx = {}
    for key, value in sources.items():
        src_url_to_idx[value['url']] = key
    all_props = {
        'metadata_sources': sources,
        'metadata_properties': {
            prop_key: {
                'values': {
                    f"{src_url_to_idx[src]}": prop_object[prop_key]
                    for src, prop_object in all_props.items()
                    if prop_key in prop_object
                },
            }
            for prop_key in prop_names
        }
    }
    for prop_key, prop_object in all_props['metadata_properties'].items():
        equals_fn = PROPERTIES[prop_key].get('equals_fn', None)
        prop_object['equal_or_null'] = prop_equals_or_none(prop_object['values'].values(), equals_fn=equals_fn)
        prop_object['equal'] = prop_equals_strict(list(prop_object['values'].values()), equals_fn=equals_fn)
    return all_props


def get_same_or_missing_prop_names(prop_names, comparison):
    prop_names = [
        pn for pn in prop_names
        if (pn in comparison['metadata_properties'] and comparison['metadata_properties'][pn]['equal']) or (
            pn not in comparison['metadata_properties'])
    ]
    # current_app.logger.info(f'prop_names after filtering: {prop_names}')
    return prop_names


def is_empty(value, prop_name):
    return value is None or PROPERTIES[prop_name].get('empty_fn', lambda _: False)(value)
