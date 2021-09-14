import pytest
from . import launder_attribute_name


@pytest.mark.parametrize('raw_attr_name, exp_output', [
    ('ABCd', 'abcd'),
    ('ABCD EFG', 'abcd efg'),
    ('NEČíslo', 'neČíslo'),
    ('ČÍSLO', 'ČÍslo'),
    ('x,', 'x,'),
])
def test_launder_attribute_name(raw_attr_name, exp_output):
    assert launder_attribute_name(raw_attr_name) == exp_output
