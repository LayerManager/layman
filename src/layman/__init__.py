from flask import Flask, redirect, jsonify

import os
import importlib

settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']


def _is_ip_address(maybe_ip):
    import socket
    try:
        socket.inet_aton(maybe_ip)
        return True
    except socket.error:
        return False


if "." in settings.LAYMAN_PROXY_SERVER_NAME and not _is_ip_address(settings.LAYMAN_PROXY_SERVER_NAME):
    app.config['SERVER_NAME'] = settings.LAYMAN_PROXY_SERVER_NAME


from .http import LaymanError
from .make_celery import make_celery
celery_app = make_celery(app)


from .util import get_blueprints
for bp in get_blueprints():
    app.register_blueprint(bp, url_prefix='/rest/<username>')

from .user.rest_current_user import bp as current_user_bp
app.register_blueprint(current_user_bp, url_prefix='/rest/current-user')

# load UUIDs only once
REDIS_LOADED_KEY = f"{__name__}:REDIS_LOADED"
if settings.LAYMAN_REDIS.get(REDIS_LOADED_KEY) is None:
    settings.LAYMAN_REDIS.set(REDIS_LOADED_KEY, 'true')
    app.logger.info(f'Loading Redis database')
    with app.app_context():
        from .uuid import import_uuids_to_redis
        import_uuids_to_redis()
        from .authn.redis import import_authn_to_redis
        import_authn_to_redis()


@app.route('/')
def index():
    return redirect(settings.LAYMAN_CLIENT_PUBLIC_URL)


@app.errorhandler(LaymanError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response