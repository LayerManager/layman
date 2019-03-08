import importlib
import re
from collections import OrderedDict

from flask import current_app

from layman.http import LaymanError
from layman.settings import *

USERNAME_RE = r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"


def check_username(username):
    if not re.match(USERNAME_RE, username):
        raise LaymanError(2, {'parameter': 'user', 'expected': USERNAME_RE})
    providers = get_providers()
    fn_name = 'check_username'
    for m in providers:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            fn(username)
        else:
            current_app.logger.warn(
                f'Module {m.__name__} does not have {fn_name} method.')


def get_sources():
    key = 'layman.sources'
    if key not in current_app.config:
        active_sources = list(map(
            lambda path: importlib.import_module(path),
            SOURCES
        ))
        current_app.config[key] = active_sources
    return current_app.config[key]

def get_providers():
    key = 'layman.providers'
    if key not in current_app.config:
        paths = list(OrderedDict.fromkeys(map(
            lambda src: src[:src.rfind('.')],
            SOURCES
        )))
        providers = list(map(
            lambda path: importlib.import_module(path),
            paths
        ))
        current_app.config[key] = providers
    return current_app.config[key]


def call_modules_fn(modules, fn_name, args=None, kwargs=None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    results = []
    for m in modules:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            results.append(fn(*args, **kwargs))
        else:
            raise Exception(
                f'Module {m.__name__} does not have {fn_name} method.')

    return results

