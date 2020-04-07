from . import language


def test_get_language():
    lang = language.get_language_iso639_2("Administrativní členění Libereckého kraje")
    assert lang == 'cze'
    lang = language.get_language_iso639_2("Na tematické mapě při přiblížení jsou postupně zobrazované administrativní celky Libereckého kraje : okresy, OPÚ, ORP a obce.")
    assert lang == 'cze'
    lang = language.get_language_iso639_2("Na mapě jsou zobrazené třídy ochrany půdy v Libereckém kraji")
    assert lang == 'cze'
    lang = language.get_language_iso639_2("Třídy ochrany půdy")
    assert lang == 'cze'

    lang = language.get_language_iso639_2("ne_110m_admin_0_countries")
    assert lang == 'eng'

    lang = language.get_language_iso639_2("ne1_110m_2admin_0_countries3")
    assert lang is None
    lang = language.get_language_iso639_2(None)
    assert lang is None
    lang = language.get_language_iso639_2('')
    assert lang is None


def test_tokenize():
    t = language.tokenize('ne_110m-admin 0+countries')
    assert t == ['ne', 'admin', 'countries']
