import re
import pycld2


SPLIT_PATTERN = re.compile(r'[\W_]', re.U)
NUMBER_PATTERN = re.compile(r'^.*\d+.*$')

# https://cs.wikipedia.org/wiki/Seznam_kódů_ISO_639-1
LANGUAGE_CODES = {
  "aa": "aar",
  "ab": "abk",
  "ae": "ave",
  "af": "afr",
  "ak": "aka",
  "am": "amh",
  "an": "arg",
  "ar": "ara",
  "as": "asm",
  "av": "ava",
  "ay": "aym",
  "az": "aze",
  "ba": "bak",
  "be": "bel",
  "bg": "bul",
  "bh": "bih",
  "bi": "bis",
  "bm": "bam",
  "bn": "ben",
  "bo": "tib",
  "br": "bre",
  "bs": "bos",
  "ca": "cat",
  "ce": "che",
  "ch": "cha",
  "co": "cos",
  "cr": "cre",
  "cs": "cze",
  "cu": "chu",
  "cv": "chv",
  "cy": "wel",
  "da": "dan",
  "de": "ger",
  "dv": "div",
  "dz": "dzo",
  "ee": "ewe",
  "el": "gre",
  "en": "eng",
  "eo": "epo",
  "es": "spa",
  "et": "est",
  "eu": "baq",
  "fa": "per",
  "ff": "ful",
  "fi": "fin",
  "fj": "fij",
  "fo": "fao",
  "fr": "fre",
  "fy": "fry",
  "ga": "gle",
  "gd": "gla",
  "gl": "glg",
  "gn": "grn",
  "gu": "guj",
  "gv": "glv",
  "ha": "hau",
  "he": "heb",
  "hi": "hin",
  "ho": "hmo",
  "hr": "scr",
  "ht": "hat",
  "hu": "hun",
  "hy": "arm",
  "hz": "her",
  "ia": "ina",
  "id": "ind",
  "ie": "ile",
  "ig": "ibo",
  "ii": "iii",
  "ik": "ipk",
  "io": "ido",
  "is": "ice",
  "it": "ita",
  "iu": "iku",
  "ja": "jpn",
  "jv": "jav",
  "ka": "geo",
  "kg": "kon",
  "ki": "kik",
  "kj": "kua",
  "kk": "kaz",
  "kl": "kal",
  "km": "khm",
  "kn": "kan",
  "ko": "kor",
  "kr": "kau",
  "ks": "kas",
  "ku": "kur",
  "kv": "kom",
  "kw": "cor",
  "ky": "kir",
  "la": "lat",
  "lb": "ltz",
  "lg": "lug",
  "li": "lim",
  "ln": "lin",
  "lo": "lao",
  "lt": "lit",
  "lu": "lub",
  "lv": "lav",
  "mg": "mlg",
  "mh": "mah",
  "mi": "mao",
  "mk": "mac",
  "ml": "mal",
  "mn": "mon",
  "mo": "mol",
  "mr": "mar",
  "ms": "may",
  "mt": "mlt",
  "my": "bur",
  "na": "nau",
  "nb": "nob",
  "nd": "nde",
  "ne": "nep",
  "ng": "ndo",
  "nl": "dut",
  "nn": "nno",
  "no": "nor",
  "nr": "nbl",
  "nv": "nav",
  "ny": "nya",
  "oc": "oci",
  "oj": "oji",
  "om": "orm",
  "or": "ori",
  "os": "oss",
  "pa": "pan",
  "pi": "pli",
  "pl": "pol",
  "ps": "pus",
  "pt": "por",
  "qu": "que",
  "rm": "roh",
  "rn": "run",
  "ro": "rum",
  "ru": "rus",
  "rw": "kin",
  "sa": "san",
  "sc": "srd",
  "sd": "snd",
  "se": "sme",
  "sg": "sag",
  "si": "sin",
  "sk": "slo",
  "sl": "slv",
  "sm": "smo",
  "sn": "sna",
  "so": "som",
  "sq": "alb",
  "sr": "scc",
  "ss": "ssw",
  "st": "sot",
  "su": "sun",
  "sv": "swe",
  "sw": "swa",
  "ta": "tam",
  "te": "tel",
  "tg": "tgk",
  "th": "tha",
  "ti": "tir",
  "tk": "tuk",
  "tl": "tgl",
  "tn": "tsn",
  "to": "ton",
  "tr": "tur",
  "ts": "tso",
  "tt": "tat",
  "tw": "twi",
  "ty": "tah",
  "ug": "uig",
  "uk": "ukr",
  "ur": "urd",
  "uz": "uzb",
  "ve": "ven",
  "vi": "vie",
  "vo": "vol",
  "wa": "wln",
  "wo": "wol",
  "xh": "xho",
  "yi": "yid",
  "yo": "yor",
  "za": "zha",
  "zh": "chi",
  "zu": "zul"
}


def tokenize(text):
    if text is None:
        return []
    tokens = SPLIT_PATTERN.split(text)
    tokens = [
        t for t in tokens
        if len(t) > 0 and not NUMBER_PATTERN.match(t)
    ]
    return tokens


def get_language_cld2(text):

    # text = text.encode("utf-8")
    tokens = tokenize(text)
    # print('tokens', tokens)
    if len(tokens) == 0:
        return None
    text = ' '.join(tokens)
    result = None
    reliable, text_bytes_found, details = pycld2.detect(text, bestEffort=False)
    # print(reliable, text_bytes_found, details)

    if not reliable:
        # print('not reliable', reliable, text_bytes_found, details)
        reliable, text_bytes_found, details = pycld2.detect(text, bestEffort=True)

    langs = []
    if reliable:
        langs = [
            d[1] for d in details
            if d[1] != 'un'
        ]
    if len(langs) > 0:
        result = langs[0]

    return result


def get_language_iso639_2(text):
    lang = get_language_cld2(text)
    return LANGUAGE_CODES.get(lang, None)