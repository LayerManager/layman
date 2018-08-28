import importlib
import re
import unicodedata

from flask import current_app
from unidecode import unidecode

from layman.http import LaymanError
from layman.settings import *

USERNAME_RE = r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"
LAYERNAME_RE = USERNAME_RE


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


def check_username(username):
    if not re.match(USERNAME_RE, username):
        raise LaymanError(2, {'parameter': 'user', 'expected': USERNAME_RE})
    active_sources = get_sources()
    fn_name = 'check_username'
    for m in active_sources:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            fn(username)
        else:
            current_app.logger.warn(
                'Module {} does not have {} method.'.format(m.__name__,
                                                            fn_name))


def check_layername(layername):
    if not re.match(LAYERNAME_RE, layername):
        raise LaymanError(2, {'parameter': 'layername', 'expected':
            LAYERNAME_RE})

def get_sources():
    key = 'layman.sources'
    if key not in current_app.config:
        active_sources = list(map(
            lambda path: importlib.import_module(path),
            SOURCES
        ))
        current_app.config[key] = active_sources
    return current_app.config[key]

def get_layer_names(username):
    layernames = []
    active_sources = get_sources()
    fn_name = 'get_layer_names'
    for m in active_sources:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            layernames += fn(username)
        else:
            current_app.logger.warn(
                'Module {} does not have {} method.'.format(m.__name__,
                                                            fn_name))
    layernames = list(set(layernames))
    return layernames

def get_layer_info(username, layername):
    info = {}
    active_sources = get_sources()
    fn_name = 'get_layer_info'
    for m in active_sources:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            info.update(fn(username, layername))
        else:
            current_app.logger.warn(
                'Module {} does not have {} method.'.format(m.__name__,
                                                            fn_name))
    return info
