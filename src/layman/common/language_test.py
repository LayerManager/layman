from . import language


def test_get_language():
    langs = language.get_languages_iso639_2("Administrativní členění Libereckého kraje")
    assert len(langs) == 1 and langs[0] == 'cze'
    langs = language.get_languages_iso639_2("Na tematické mapě při přiblížení jsou postupně zobrazované administrativní celky Libereckého kraje : okresy, OPÚ, ORP a obce.")
    assert len(langs) == 1 and langs[0] == 'cze'
    langs = language.get_languages_iso639_2("Na mapě jsou zobrazené třídy ochrany půdy v Libereckém kraji")
    assert len(langs) == 1 and langs[0] == 'cze'
    langs = language.get_languages_iso639_2("Třídy ochrany půdy")
    assert len(langs) == 1 and langs[0] == 'cze'

    langs = language.get_languages_iso639_2("ne_110m_admin_0_countries")
    assert len(langs) == 1 and langs[0] == 'eng'

    langs = language.get_languages_iso639_2("ne1_110m_2admin_0_countries3")
    assert len(langs) == 0
    langs = language.get_languages_iso639_2(None)
    assert len(langs) == 0
    langs = language.get_languages_iso639_2('')
    assert len(langs) == 0


def test_tokenize():
    t = language.tokenize('ne_110m-admin 0+countries')
    assert t == ['ne', 'admin', 'countries']
