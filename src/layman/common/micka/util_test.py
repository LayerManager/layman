import sys
del sys.modules['layman']

from .util import parse_md_properties, prop_equals
from . import PROPERTIES as MICKA_PROPERTIES
from layman.common.metadata import PROPERTIES as COMMON_PROPERTIES


def test_fill_template():
    xml_path = 'src/layman/layer/micka/util_test_filled_template.xml'
    with open(xml_path, 'r') as xml_file:
        props = parse_md_properties(xml_file, MICKA_PROPERTIES.keys())
    expected = {
        'md_file_identifier': 'm-ca238200-8200-1a23-9399-42c9fca53542',
        'md_date_stamp': '2007-05-25',
        'reference_system': ['EPSG:4326', 'EPSG:3857'],
        'title': 'CORINE - Krajinný pokryv CLC 90',
        'publication_date': '2007-05-25',
        'identifier': 'http://www.env.cz/data/corine/1990',
        'abstract': None,
        'graphic_url': 'http://layman_test_run_1:8000/rest/browser/layers/layer/thumbnail',
        'extent': [11.87, 19.13, 48.12, 51.59],
        'wms_url': 'http://www.env.cz/corine/data/download.zip',
        'wfs_url': 'http://www.env.cz/corine/data/download.zip',
        'layer_endpoint': 'http://layman_test_run_1:8000/rest/browser/layers/layer',
    }
    assert set(props.keys()) == set(expected.keys())
    for k in props.keys():
        equals_fn = COMMON_PROPERTIES[k].get('equals_fn', None)
        assert prop_equals(props[k], expected[k], equals_fn), f"Values of property {k} do not equal: {props[k]} != {expected[k]}"
