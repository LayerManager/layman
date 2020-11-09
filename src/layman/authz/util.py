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
    return None


def get_publication_access_rights(publ_type, username, publication_name):
    authz_module = get_authz_module()
    return authz_module.get_publication_access_rights(publ_type, username, publication_name)


def get_all_gs_roles(username, type):
    rewe_roles = read_everyone_write_everyone.get_gs_roles(username, type)
    rewo_roles = read_everyone_write_owner.get_gs_roles(username, type)
    all_roles = set.union(rewe_roles, rewo_roles)

    return all_roles


def setup_patch_access_rights(request_form, kwargs):
    for type in ['read', 'write']:
        if request_form.get('access_rights.' + type):
            kwargs['access_rights'] = kwargs.get('access_rights', dict())
            access_rights = list({x.strip() for x in request_form['access_rights.' + type].split(',')})
            kwargs['access_rights'][type] = access_rights


def setup_post_access_rights(request_form, kwargs, actor_name):
    kwargs['access_rights'] = dict()
    for type in ['read', 'write']:
        if not request_form.get('access_rights.' + type):
            if actor_name:
                access_rights = [actor_name]
            else:
                access_rights = [settings.RIGHTS_EVERYONE_ROLE]
        else:
            access_rights = list({x.strip() for x in request_form['access_rights.' + type].split(',')})
        kwargs['access_rights'][type] = access_rights
