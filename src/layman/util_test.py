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


def test_check_reserved_workspace_names():
    with app.app_context():
        for username in settings.RESERVED_WORKSPACE_NAMES:
            with pytest.raises(LaymanError) as exc_info:
                util.check_reserved_workspace_names(username)
            assert exc_info.value.code == 35
            assert exc_info.value.data['reserved_by'] == 'RESERVED_WORKSPACE_NAMES'
