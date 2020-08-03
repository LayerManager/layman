import importlib
from functools import wraps
from flask import current_app

from layman import settings
from layman.util import call_modules_fn

FLASK_MODULE_KEY = f'{__name__}:MODULE'


def authorize(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # print(f"authorize ARGS {args} KWARGS {kwargs}")
        authz_module = get_authz_module()
        call_modules_fn([authz_module], 'authorize')
        return f(*args, **kwargs)

    return decorated_function


def get_authz_module():
    key = FLASK_MODULE_KEY
    if key not in current_app.config:
        current_app.config[key] = importlib.import_module(settings.AUTHZ_MODULE)
    return current_app.config[key]


def get_publication_access_rights(publ_type, username, publication_name):
    authz_module = get_authz_module()
    return authz_module.get_publication_access_rights(publ_type, username, publication_name)
