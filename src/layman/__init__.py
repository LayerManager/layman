from flask import Flask, redirect, jsonify

import os
import importlib
import sys
import time


IN_CELERY_WORKER_PROCESS = sys.argv and sys.argv[0].endswith('/celery/__main__.py')
IN_PYTEST_PROCESS = sys.argv and sys.argv[0].endswith('/pytest/__main__.py')
IN_FLOWER_PROCESS = sys.argv and sys.argv[0].endswith('/flower/__main__.py')
IN_FLASK_PROCESS = sys.argv and (sys.argv[0].endswith('/flask') or sys.argv[0].endswith('/gunicorn'))
assert [
    IN_CELERY_WORKER_PROCESS,
    IN_PYTEST_PROCESS,
    IN_FLOWER_PROCESS,
    IN_FLASK_PROCESS,
].count(True) == 1, f"IN_CELERY_WORKER_PROCESS={IN_CELERY_WORKER_PROCESS}, IN_PYTEST_PROCESS={IN_PYTEST_PROCESS}, IN_FLOWER_PROCESS={IN_FLOWER_PROCESS}, IN_FLASK_PROCESS={IN_FLASK_PROCESS}"

settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']
app.config['PREFERRED_URL_SCHEME'] = settings.LAYMAN_PUBLIC_URL_SCHEME

from .http import LaymanError
from .make_celery import make_celery

celery_app = make_celery(app)

from .util import get_blueprints

for bp in get_blueprints():
    app.register_blueprint(bp, url_prefix='/rest/<username>')

from .user.rest_current_user import bp as current_user_bp
from .gs_wfs_proxy import bp as gs_wfs_proxy_bp
from .common import prime_db_schema as db_util

app.register_blueprint(current_user_bp, url_prefix='/rest/current-user')
app.register_blueprint(gs_wfs_proxy_bp, url_prefix='/geoserver')

app.logger.info(f"IN_CELERY_WORKER_PROCESS={IN_CELERY_WORKER_PROCESS}")
app.logger.info(f"IN_PYTEST_PROCESS={IN_PYTEST_PROCESS}")
app.logger.info(f"IN_FLOWER_PROCESS={IN_FLOWER_PROCESS}")
app.logger.info(f"IN_FLASK_PROCESS={IN_FLASK_PROCESS}")

# load UUIDs only once
LAYMAN_DEPS_ADJUSTED_KEY = f"{__name__}:LAYMAN_DEPS_ADJUSTED"
if settings.LAYMAN_REDIS.get(LAYMAN_DEPS_ADJUSTED_KEY) != 'done':
    if (IN_FLASK_PROCESS or IN_PYTEST_PROCESS) and settings.LAYMAN_REDIS.get(LAYMAN_DEPS_ADJUSTED_KEY) is None:
        settings.LAYMAN_REDIS.set(LAYMAN_DEPS_ADJUSTED_KEY, 'processing')

        app.logger.info(f'Adjusting GeoServer')
        with app.app_context():
            from layman.common.geoserver import ensure_role, ensure_user, ensure_user_role, ensure_wms_srs_list, ensure_proxy_base_url
            if settings.GEOSERVER_ADMIN_AUTH:
                ensure_role(settings.LAYMAN_GS_ROLE, settings.GEOSERVER_ADMIN_AUTH)
                ensure_user(settings.LAYMAN_GS_USER, settings.LAYMAN_GS_PASSWORD, settings.GEOSERVER_ADMIN_AUTH)
                ensure_user_role(settings.LAYMAN_GS_USER, 'ADMIN', settings.GEOSERVER_ADMIN_AUTH)
                ensure_user_role(settings.LAYMAN_GS_USER, settings.LAYMAN_GS_ROLE, settings.GEOSERVER_ADMIN_AUTH)
            ensure_wms_srs_list([int(srs.split(':')[1]) for srs in settings.INPUT_SRS_LIST], settings.LAYMAN_GS_AUTH)
            if settings.LAYMAN_GS_PROXY_BASE_URL != '':
                ensure_proxy_base_url(settings.LAYMAN_GS_PROXY_BASE_URL, settings.LAYMAN_GS_AUTH)

        with app.app_context():
            db_util.check_schema_name()
        with app.app_context():
            db_util.ensure_schema()

        app.logger.info(f'Loading Redis database')
        with app.app_context():
            from .uuid import import_uuids_to_redis

            import_uuids_to_redis()
            from .authn.redis import import_authn_to_redis

            import_authn_to_redis()
        settings.LAYMAN_REDIS.set(LAYMAN_DEPS_ADJUSTED_KEY, 'done')

        app.logger.info(f'Ensuring users')
        from .util import get_usernames, ensure_whole_user, check_username
        with app.app_context():
            for username in get_usernames():
                app.logger.info(f'Ensuring user {username}')
                check_username(username)
                ensure_whole_user(username)

    else:
        while(settings.LAYMAN_REDIS.get(LAYMAN_DEPS_ADJUSTED_KEY) != 'done'):
            app.logger.info(f'Waiting for flask process to adjust dependencies')
            time.sleep(1)


@app.route('/')
def index():
    return redirect(settings.LAYMAN_CLIENT_PUBLIC_URL)


@app.errorhandler(LaymanError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response
