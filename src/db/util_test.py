import pytest

from . import util


@pytest.mark.parametrize('input_string, exp_result', [
    ('Příliš žluťoučký kůň úpěl ďábelské ódy', 'Příliš | žluťoučký | kůň | úpěl | ďábelské | ódy'),
    (' #@ Příliš žluťoučký kůň úpěl ďábelské ódy  \n', 'Příliš | žluťoučký | kůň | úpěl | ďábelské | ódy'),
    ('Pří_liš', 'Pří | liš'),
    ('\'Too yellow horse\' means "Příliš žluťoučký kůň".', 'Too | yellow | horse | means | Příliš | žluťoučký | kůň'),
    ('\tThe Fačřš_tÚŮTŤsa   "  a34432[;] ;.\\Ra\'\'ts  ', 'The | Fačřš | tÚŮTŤsa | a34432 | Ra | ts'),
])
def test_to_tsquery_string(input_string, exp_result):
    assert util.to_tsquery_string(input_string) == exp_result
