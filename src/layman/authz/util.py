import importlib
from functools import wraps
from flask import current_app

from layman import settings
from layman.util import call_modules_fn
from layman.authz import read_everyone_write_everyone
from layman.authz import read_everyone_write_owner

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


def get_all_GS_roles(username, type):
    roles = set()
    roles.union(read_everyone_write_everyone.get_GS_roles(username, type))
    roles.union(read_everyone_write_owner.get_GS_roles(username, type))

    authz_module = get_authz_module()
    roles = roles.difference_update(authz_module.get_GS_roles(username, type))
    return roles
