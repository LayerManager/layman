import sys
del sys.modules['layman']

from . import util


def test_get_default_values_dict():
    defaults = util.get_default_values_dict()
    assert '_TODO' not in defaults


def test_fill_template():
    xmlstr = util.fill_template('src/layman/metadata/INSPIRE2-min.template.xml', filled_path='src/layman/metadata/INSPIRE2-min.xml')
