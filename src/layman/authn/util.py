from functools import wraps
from flask import g, current_app, request

from layman import LaymanError, settings
from layman.util import call_modules_fn, get_modules_from_names

FLASK_MODULES_KEY = f'{__name__}:MODULES'


def authenticate(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        # pylint: disable=assigning-non-slot
        # current_app.logger.info(f"authenticate ARGS {args} KWARGS {kwargs}")
        authn_modules = get_authn_modules()
        results = list(call_modules_fn(authn_modules, 'authenticate', until=lambda r: r is not None).values())
        authenticated = len(results) > 0 and results[-1] is not None
        if authenticated:
            authn_module = authn_modules[len(results) - 1]
            g.user['AUTHN_MODULE'] = authn_module.__name__
        else:
            g.user = None
        return function(*args, **kwargs)

    return decorated_function


def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        # print(f"login_required ARGS {args} KWARGS {kwargs}")
        if g.user is None:
            raise LaymanError(30)
        return function(*args, **kwargs)

    return decorated_function


def get_open_id_claims():
    user = g.user
    if user is None:
        result = {
            'iss': request.host_url,
            'name': 'Anonymous',
            'nickname': 'Anonymous',
        }
    else:
        authn_module = get_authn_module()
        result = authn_module.get_open_id_claims()
    # pylint: disable=assigning-non-slot
    g.open_id_claims = result
    return result


def get_authn_module():
    user = g.user
    authn_module = user['AUTHN_MODULE']
    authn_module = next((m for m in get_authn_modules() if m.__name__ == authn_module))
    return authn_module


def get_authn_module_by_iss_id(iss_id):
    authn_module = next((m for m in get_authn_modules() if m.get_iss_id() == iss_id), None)
    return authn_module


def get_iss_id():
    authn_module = get_authn_module()
    return authn_module.get_iss_id()


def get_sub():
    authn_module = get_authn_module()
    return authn_module.get_sub()


def flush_cache():
    authn_module = get_authn_module()
    return authn_module.flush_cache()


def get_authn_modules():
    key = FLASK_MODULES_KEY
    if key not in current_app.config:
        current_app.config[key] = get_modules_from_names(settings.LAYMAN_AUTHN_MODULES)
    return current_app.config[key]
