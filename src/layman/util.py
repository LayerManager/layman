import re
import unicodedata

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
