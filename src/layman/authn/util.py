from functools import wraps
from flask import g, current_app

from layman import LaymanError, settings
from layman.util import call_modules_fn, get_modules_from_names

FLASK_MODULES_KEY = f'{__name__}:MODULES'

def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # print(f"authenticate ARGS {args} KWARGS {kwargs}")
        authn_modules = get_authn_modules()
        if len(authn_modules) == 0:
            raise Exception('At least one authentication module must be set (see AUTHN_MODULES).')
        results = call_modules_fn(authn_modules, 'authenticate', until=lambda r: r is not None)
        authenticated = results[-1] is not None
        if authenticated:
            authn_module = authn_modules[len(results) - 1]
            g.user['AUTHN_MODULE'] = authn_module.__name__
        #     TODO also read user's profile
        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # print(f"login_required ARGS {args} KWARGS {kwargs}")
        if g.user is None:
            raise LaymanError(1)
        return f(*args, **kwargs)
    return decorated_function


def get_authn_modules():
    key = FLASK_MODULES_KEY
    if key not in current_app.config:
        current_app.config[key] = get_modules_from_names(settings.AUTHN_MODULES)
    return current_app.config[key]