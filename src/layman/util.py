import re, os, unicodedata
from unidecode import unidecode
from .settings import *


def slugify(value):
    value = unidecode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s\-\.]', '', value).lower()
    value = re.sub(r'[\s\-\._]+', '_', value).strip('_')
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

def get_layman_rules(all_rules, layman_role=LAYMAN_GS_ROLE):
    re_role = r".*\b" + re.escape(layman_role) + r"\b.*"
    result = {k: v for k, v in all_rules.items() if re.match(re_role, v)}
    return result

def get_non_layman_workspaces(all_workspaces, layman_rules):
    result = [
        ws for ws in all_workspaces
        if next((
            k for k in layman_rules
            if re.match(r"^" + re.escape(ws['name']) + r"\..*", k)
        ), None) is None
    ]
    return result
