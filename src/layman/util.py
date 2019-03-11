import importlib
import re
from collections import OrderedDict

from flask import current_app

from layman.http import LaymanError
from layman import settings

USERNAME_RE = r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"


def check_username(username):
    if not re.match(USERNAME_RE, username):
        raise LaymanError(2, {'parameter': 'user', 'expected': USERNAME_RE})
    providers = get_internal_providers()
    call_modules_fn(providers, 'check_username', [username])


def get_internal_providers():
    key = 'layman.providers'
    if key not in current_app.config:
        all_sources = []
        for publ_module in get_publication_modules():
            for type_def in publ_module.PUBLICATION_TYPES.values():
                all_sources += type_def['internal_sources']
        current_app.config[key] = get_providers_from_source_names(all_sources)
    return current_app.config[key]


def get_blueprints():
    blueprints = []
    for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
        for type_def in publ_module.PUBLICATION_TYPES.values():
            blueprints += type_def['blueprints']
    return blueprints


def get_publication_modules():
    key = 'layman.publication_modules'
    if key not in current_app.config:
        current_app.config[key] = get_modules_from_names(settings.PUBLICATION_MODULES)
    return current_app.config[key]


def get_providers_from_source_names(source_names):
    provider_names = list(OrderedDict.fromkeys(map(
        lambda src: src[:src.rfind('.')],
        source_names
    )))
    provider_names = list(set(provider_names))
    providers = get_modules_from_names(provider_names)
    return providers


def get_modules_from_names(module_names):
    modules = list(map(
        lambda module_name: importlib.import_module(module_name),
        module_names
    ))
    return modules


def call_modules_fn(modules, fn_name, args=None, kwargs=None, omit_duplicate_calls=True):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    fns = []
    for m in modules:
        fn = getattr(m, fn_name, None)
        if fn is None:
            raise Exception(
                f'Module {m.__name__} does not have {fn_name} method.')
        if fn not in fns or not omit_duplicate_calls:
            fns.append(fn)

    results = []
    for fn in fns:
        results.append(fn(*args, **kwargs))

    return results

