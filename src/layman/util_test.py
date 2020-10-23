import pytest

from . import app as app, LaymanError, settings
from . import util
from .util import slugify


def test_slugify():
    assert slugify('Brno-město') == 'brno_mesto'
    assert slugify('Brno__město') == 'brno_mesto'
    assert slugify(' ') == ''
    assert slugify(' ?:"+  @') == ''
    assert slugify('01 Stanice vodních toků 26.4.2017 (voda)') == \
        '01_stanice_vodnich_toku_26_4_2017_voda'


def test_check_username_rest_prefix():
    with app.app_context():
        for username in settings.RESERVED_USERNAMES:
            with pytest.raises(LaymanError) as exc_info:
                util.check_username_rest_prefix(username)
            assert exc_info.value.code == 43
