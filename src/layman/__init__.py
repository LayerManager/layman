from flask import Flask, redirect, jsonify

import os
import importlib

settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])

from .http import LaymanError
from .make_celery import make_celery

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

celery_app = make_celery(app)


from .util import get_blueprints
for bp in get_blueprints():
    app.register_blueprint(bp, url_prefix='/rest/<username>')

from .user.current_user import bp as current_user_bp
app.register_blueprint(current_user_bp, url_prefix='/rest/current-user')

# load UUIDs only once
if not settings.IS_CELERY_WORKER and os.getenv('LAYMAN_SKIP_REDIS_LOADING', 'false').lower() != 'true':
    os.environ['LAYMAN_SKIP_REDIS_LOADING'] = 'true'
    with app.app_context():
        from .uuid import import_uuids_to_redis
        import_uuids_to_redis()


@app.route('/')
def index():
    return redirect('/static/test-client/index.html')


@app.errorhandler(LaymanError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response