from functools import wraps
from flask import g

from layman import LaymanError
from layman.util import get_authn_modules, call_modules_fn


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


