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

def get_file_name_mappings(file_names, main_file_name, layer_name, user_dir):
    main_file_name = os.path.splitext(main_file_name)[0]
    filename_mapping = {}
    filepath_mapping = {}
    for file_name in file_names:
        if file_name.startswith(main_file_name + '.'):
            new_fn = layer_name + file_name[len(main_file_name):]
            filepath_mapping[file_name] = os.path.join(user_dir, new_fn)
            filename_mapping[file_name] = new_fn
        else:
            filename_mapping[file_name] = None
            filepath_mapping[file_name] = None
    return (filename_mapping, filepath_mapping)
