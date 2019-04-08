from .util import to_safe_layer_name


def test_to_safe_layer_name():
    assert to_safe_layer_name('') == 'layer'
    assert to_safe_layer_name(' ?:"+  @') == 'layer'
    assert to_safe_layer_name('01 Stanice vodních toků 26.4.2017 (voda)') == \
           'layer_01_stanice_vodnich_toku_26_4_2017_voda'


