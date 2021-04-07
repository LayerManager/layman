import os
import importlib
import sys
import time
from flask import Flask, redirect, jsonify
from flask.logging import create_logger

from redis import WatchError

IN_CELERY_WORKER_PROCESS = sys.argv and sys.argv[0].endswith('/celery/__main__.py')
IN_PYTEST_PROCESS = sys.argv and sys.argv[0].endswith('/pytest/__main__.py')
IN_FLOWER_PROCESS = sys.argv and sys.argv[0].endswith('/flower/__main__.py')
IN_FLASK_PROCESS = sys.argv and (sys.argv[0].endswith('/flask') or sys.argv[0].endswith('/gunicorn'))
IN_UPGRADE_PROCESS = sys.argv and sys.argv[0].endswith('standalone_upgrade.py')
IN_UTIL_PROCESS = sys.argv and sys.argv[0].endswith('refresh-doc-metadata-xpath.py')
assert [
    IN_CELERY_WORKER_PROCESS,
    IN_PYTEST_PROCESS,
    IN_FLOWER_PROCESS,
    IN_FLASK_PROCESS,
    IN_UPGRADE_PROCESS,
    IN_UTIL_PROCESS,
].count(True) == 1, f"IN_CELERY_WORKER_PROCESS={IN_CELERY_WORKER_PROCESS}, IN_PYTEST_PROCESS={IN_PYTEST_PROCESS}, IN_FLOWER_PROCESS={IN_FLOWER_PROCESS}, IN_FLASK_PROCESS={IN_FLASK_PROCESS}, IN_UPGRADE_PROCESS={IN_UPGRADE_PROCESS}, IN_UTIL_PROCESS={IN_UTIL_PROCESS}"

settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']
app.config['PREFERRED_URL_SCHEME'] = settings.LAYMAN_PUBLIC_URL_SCHEME
logger = create_logger(app)

from .http import LaymanError
from .make_celery import make_celery

celery_app = make_celery(app)

from .util import get_workspace_blueprints, get_blueprints

for bp in get_workspace_blueprints():
    app.register_blueprint(bp, url_prefix=f'/rest/{settings.REST_WORKSPACES_PREFIX}/<username>')
    app.register_blueprint(bp, url_prefix='/rest/<username>')

for bp in get_blueprints():
    app.register_blueprint(bp, url_prefix=f'/rest')

from .user.rest_current_user import bp as current_user_bp
from .geoserver_proxy import bp as geoserver_proxy_bp
from .user.rest_users import bp as users_bp

app.register_blueprint(current_user_bp, url_prefix='/rest/current-user')
app.register_blueprint(geoserver_proxy_bp, url_prefix='/geoserver')
app.register_blueprint(users_bp, url_prefix=f'/rest/{settings.REST_USERS_PREFIX}')

logger.info(f"IN_CELERY_WORKER_PROCESS={IN_CELERY_WORKER_PROCESS}")
logger.info(f"IN_PYTEST_PROCESS={IN_PYTEST_PROCESS}")
logger.info(f"IN_FLOWER_PROCESS={IN_FLOWER_PROCESS}")
logger.info(f"IN_FLASK_PROCESS={IN_FLASK_PROCESS}")
logger.info(f"IN_UPGRADE_PROCESS={IN_UPGRADE_PROCESS}")
logger.info(f"IN_UTIL_PROCESS={IN_UTIL_PROCESS}")

# load UUIDs only once
LAYMAN_DEPS_ADJUSTED_KEY = f"{__name__}:LAYMAN_DEPS_ADJUSTED"

with settings.LAYMAN_REDIS.pipeline() as pipe:
    wait_for_other_process = False
    try:
        pipe.watch(LAYMAN_DEPS_ADJUSTED_KEY)

        if settings.LAYMAN_REDIS.get(LAYMAN_DEPS_ADJUSTED_KEY) != 'done':
            pipe.multi()
            rds_key_value = settings.LAYMAN_REDIS.get(LAYMAN_DEPS_ADJUSTED_KEY)
            if (IN_FLASK_PROCESS or IN_PYTEST_PROCESS or IN_UPGRADE_PROCESS) and rds_key_value is None:
                pipe.set(LAYMAN_DEPS_ADJUSTED_KEY, 'processing')
                pipe.execute()

                with app.app_context():
                    logger.info(f'Adjusting GeoServer roles')
                    from layman.common import geoserver as gs

                    if settings.GEOSERVER_ADMIN_AUTH:
                        gs.ensure_role(settings.LAYMAN_GS_ROLE, settings.GEOSERVER_ADMIN_AUTH)
                        gs.ensure_user(settings.LAYMAN_GS_USER, settings.LAYMAN_GS_PASSWORD, settings.GEOSERVER_ADMIN_AUTH)
                        gs.ensure_user_role(settings.LAYMAN_GS_USER, 'ADMIN', settings.GEOSERVER_ADMIN_AUTH)
                        gs.ensure_user_role(settings.LAYMAN_GS_USER, settings.LAYMAN_GS_ROLE, settings.GEOSERVER_ADMIN_AUTH)

                    if not IN_UPGRADE_PROCESS:
                        logger.info(f'Adjusting GeoServer SRS')
                        any_srs_list_changed = False
                        for service in gs.SERVICE_TYPES:
                            service_srs_list_changed = gs.ensure_service_srs_list(service, settings.LAYMAN_OUTPUT_SRS_LIST, settings.LAYMAN_GS_AUTH)
                            any_srs_list_changed = service_srs_list_changed or any_srs_list_changed
                        if any_srs_list_changed:
                            gs.reload(settings.LAYMAN_GS_AUTH)
                        if settings.LAYMAN_GS_PROXY_BASE_URL != '':
                            gs.ensure_proxy_base_url(settings.LAYMAN_GS_PROXY_BASE_URL, settings.LAYMAN_GS_AUTH)

                        from . import upgrade
                        upgrade.upgrade()

                        logger.info(f'Loading Redis database')
                        from .uuid import import_uuids_to_redis

                        import_uuids_to_redis()
                        from .authn.redis import import_authn_to_redis

                        import_authn_to_redis()

                        logger.info(f'Ensure SRS output list for QGIS projects')
                        from .layer.qgis import output_srs
                        output_srs.ensure_output_srs_for_all()

                pipe.multi()
                pipe.set(LAYMAN_DEPS_ADJUSTED_KEY, 'done')
                pipe.execute()

            else:
                wait_for_other_process = True
    except WatchError:
        logger.info(f"WatchError during layman's startup")
        wait_for_other_process = True

    if wait_for_other_process:
        while settings.LAYMAN_REDIS.get(LAYMAN_DEPS_ADJUSTED_KEY) != 'done':
            logger.info(f'Waiting for Layman in other process to initialize dependencies')
            time.sleep(1)

from .rest_about import bp as about_bp
app.register_blueprint(about_bp, url_prefix=f'/rest/about')

logger.info(f'Layman successfully started!')


@app.route('/')
def index():
    return redirect(settings.LAYMAN_CLIENT_PUBLIC_URL)


@app.errorhandler(LaymanError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response
