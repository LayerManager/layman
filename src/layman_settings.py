import os
from urllib.parse import urljoin

IS_CELERY_WORKER = os.getenv('IS_CELERY_WORKER', '').lower() == 'true'

LAYMAN_DATA_DIR = os.environ['LAYMAN_DATA_DIR']

MAIN_FILE_EXTENSIONS = [
    '.geojson',
    '.shp'
]

INPUT_SRS_LIST = [
    'EPSG:3857',
    'EPSG:4326',
]

LAYMAN_PG_HOST = os.environ['LAYMAN_PG_HOST']
LAYMAN_PG_PORT = os.environ['LAYMAN_PG_PORT']
LAYMAN_PG_DBNAME = os.environ['LAYMAN_PG_DBNAME']
LAYMAN_PG_USER = os.environ['LAYMAN_PG_USER']
LAYMAN_PG_PASSWORD = os.environ['LAYMAN_PG_PASSWORD']

PG_CONN = f"host='{LAYMAN_PG_HOST}' port='{LAYMAN_PG_PORT}' dbname='{LAYMAN_PG_DBNAME}' user='{LAYMAN_PG_USER}' password='{LAYMAN_PG_PASSWORD}'"

LAYMAN_GS_AUTH = (os.environ['LAYMAN_GS_USER'],
                  os.environ['LAYMAN_GS_PASSWORD'])

LAYMAN_GS_HOST = os.environ['LAYMAN_GS_HOST']
LAYMAN_GS_PORT = os.environ['LAYMAN_GS_PORT']
LAYMAN_GS_PATH = os.environ['LAYMAN_GS_PATH']

LAYMAN_GS_URL = f"http://{LAYMAN_GS_HOST}:{LAYMAN_GS_PORT}{LAYMAN_GS_PATH}"

LAYMAN_GS_ROLE=os.environ['LAYMAN_GS_ROLE']

LAYMAN_GS_REST = urljoin(LAYMAN_GS_URL, 'rest/')
LAYMAN_GS_REST_STYLES = urljoin(LAYMAN_GS_REST, 'styles/')
LAYMAN_GS_REST_WORKSPACES = urljoin(LAYMAN_GS_REST, 'workspaces/')
LAYMAN_GS_REST_SETTINGS = urljoin(LAYMAN_GS_REST, 'settings/')
LAYMAN_GS_REST_SECURITY_ACL_LAYERS = urljoin(LAYMAN_GS_REST,
                                             'security/acl/layers/')

GS_RESERVED_WORKSPACE_NAMES = [
    'default',
]

# List of schemas that are owned by LAYMAN_PG_USER, but should not be used
# by layman.
# Note: Schemas as public, topology, or pg_catalog are usually owned by
# 'postgres' user, so it is not necessary to list it here.
PG_NON_USER_SCHEMAS = [
    'public',
    'topology',
]

PG_POSTGIS_SCHEMA = 'public'


# related to testing only
LAYMAN_PG_TEMPLATE_DBNAME = os.getenv('LAYMAN_PG_TEMPLATE_DBNAME')

PG_CONN_TEMPLATE = f"host='{os.environ['LAYMAN_PG_HOST']}' port='{os.environ['LAYMAN_PG_PORT']}' dbname='{LAYMAN_PG_TEMPLATE_DBNAME}' user='{os.environ['LAYMAN_PG_USER']}' password='{os.environ['LAYMAN_PG_PASSWORD']}'"

LAYMAN_CELERY_QUEUE = os.environ['LAYMAN_CELERY_QUEUE']


PUBLICATION_MODULES = [
    'layman.layer',
    'layman.map',
]


# UPLOAD_MAX_INACTIVITY_TIME = 10 # 10 seconds
UPLOAD_MAX_INACTIVITY_TIME = 5 * 60 # 5 minutes

LAYMAN_REDIS_URL = os.environ['LAYMAN_REDIS_URL']
import redis
LAYMAN_REDIS = redis.Redis.from_url(LAYMAN_REDIS_URL, encoding="utf-8", decode_responses=True)


LAYMAN_DOCKER_MAIN_SERVICE = os.environ['LAYMAN_DOCKER_MAIN_SERVICE']