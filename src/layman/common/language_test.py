from . import language


def test_get_language():
    langs = language.get_languages_iso639_2("Administrativní členění Libereckého kraje")
    assert len(langs) == 1 and langs[0] == 'cze'
    langs = language.get_languages_iso639_2(
        "Na tematické mapě při přiblížení jsou postupně zobrazované administrativní celky Libereckého kraje : okresy, OPÚ, ORP a obce.")
    assert len(langs) == 1 and langs[0] == 'cze'
    langs = language.get_languages_iso639_2("Na mapě jsou zobrazené třídy ochrany půdy v Libereckém kraji")
    assert len(langs) == 1 and langs[0] == 'cze'
    langs = language.get_languages_iso639_2("Třídy ochrany půdy")
    assert len(langs) == 1 and langs[0] == 'cze'
    langs = language.get_languages_iso639_2("добрый день")
    assert len(langs) == 1 and langs[0] == 'rus'
    langs = language.get_languages_iso639_2(
        "Ватикан Сан Марино Вадуц Лобамба Люксембург Паликир Маджуро Фунафути Мелекеок Бир Лелу Монако Морони Андорра ла Велья Порт оф Спейн Кигали Мбабане Джуба Гаага Любляна Братислава Доха Подгорица Шри Джаяварденепура Котте Багио Додома Берн Эль Аюн Приштина Розо Джибути Путраджая Киото Банжул Скопье Бриджтаун Порто Ново Бужумбура Кингстаун Кастри Бастер Порт Луи Сент Джорджес Манама Сент Джонс Монтевидео Ломе Тунис Абу Даби Ашхабад Лусака Хараре Дили Порт Вила Тегусигальпа Джорджтаун Рейкьявик Порт о Пренс Кампала Парамарибо Ниамей Душанбе Асунсьон Манагуа Фритаун Исламабад Катманду Блумфонтейн Претория Порт Морсби Хониара Панама Рабат Кишинёв Мапуту Могадишо Маскат Коломбо Улан Батор Виндхук Абуджа Бисау Амман Вильнюс Рига Бишкек Масеру Антананариву Кито Сан Хосе Сан Сальвадор Кингстон Нджамена Малабо Асмэра Загреб Таллин Лилонгве Гватемала Либревиль")
    assert len(langs) == 1 and langs[0] == 'rus'

    langs = language.get_languages_iso639_2("ne_110m_admin_0_countries")
    assert len(langs) == 1 and langs[0] == 'eng'

    langs = language.get_languages_iso639_2("ne1_110m_2admin_0_countries3")
    assert len(langs) == 0
    langs = language.get_languages_iso639_2(None)
    assert len(langs) == 0
    langs = language.get_languages_iso639_2('')
    assert len(langs) == 0


def test_tokenize():
    tokens_list = language.tokenize('ne_110m-admin 0+countries')
    assert tokens_list == ['ne', 'admin', 'countries']
