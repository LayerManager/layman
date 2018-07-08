import re, os, unicodedata
from unidecode import unidecode
from .settings import MAIN_FILE_EXTENSIONS


def slugify(value):
    value = unidecode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s\-\.]', '', value).lower()
    value = re.sub(r'[\s\-\.]+', '_', value).strip('_')
    return value


def to_safe_layer_name(value):
    value = slugify(value)
    if len(value)==0:
        value = 'layer'
    elif re.match(r'^[^a-z].*', value):
        value = 'layer_'+value
    return value

def get_main_file_name(file_names):
    return next((fn for fn in file_names if os.path.splitext(fn)[1]
          in MAIN_FILE_EXTENSIONS), None)