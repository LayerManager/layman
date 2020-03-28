import os
from urllib.parse import urljoin
from layman_settings_util import read_clients_dict_from_env

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

PG_CONN = {
    'host': LAYMAN_PG_HOST,
    'port': LAYMAN_PG_PORT,
    'dbname': LAYMAN_PG_DBNAME,
    'user': LAYMAN_PG_USER,
    'password': LAYMAN_PG_PASSWORD,
}

LAYMAN_GS_USER = os.environ['LAYMAN_GS_USER']
LAYMAN_GS_AUTH = (LAYMAN_GS_USER,
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

LAYMAN_CELERY_QUEUE = os.environ['LAYMAN_CELERY_QUEUE']


PUBLICATION_MODULES = [
    'layman.layer',
    'layman.map',
]

LAYMAN_AUTHN_MODULES = [
    m for m in os.getenv('LAYMAN_AUTHN_MODULES', '').split(',')
    if len(m) > 0
]

LAYMAN_AUTHN_OAUTH2_PROVIDERS = [
    m for m in os.getenv('LAYMAN_AUTHN_OAUTH2_PROVIDERS', '').split(',')
    if len(m) > 0
]

LAYMAN_AUTHN_CACHE_MAX_TIMEOUT = 60

OAUTH2_LIFERAY_AUTH_URLS = [
    u for u in [
        os.getenv('OAUTH2_LIFERAY_AUTH_URL', ''),
    ]
    if len(u) > 0
]
OAUTH2_LIFERAY_INTROSPECTION_URL = os.getenv('OAUTH2_LIFERAY_INTROSPECTION_URL', None)
OAUTH2_LIFERAY_USER_PROFILE_URL = os.getenv('OAUTH2_LIFERAY_USER_PROFILE_URL', None)
OAUTH2_LIFERAY_CLIENTS = [
    d for d in read_clients_dict_from_env()
    if len(d['id']) > 0
]

AUTHZ_MODULE = os.environ['LAYMAN_AUTHZ_MODULE']


# UPLOAD_MAX_INACTIVITY_TIME = 10 # 10 seconds
UPLOAD_MAX_INACTIVITY_TIME = 5 * 60 # 5 minutes

# max time (in seconds) to cache GeoServer's requests like WMS capabilities
LAYMAN_CACHE_GS_TIMEOUT = 1 * 60 # 1 minute

LAYMAN_REDIS_URL = os.environ['LAYMAN_REDIS_URL']
import redis
LAYMAN_REDIS = redis.Redis.from_url(LAYMAN_REDIS_URL, encoding="utf-8", decode_responses=True)


LAYMAN_TIMGEN_URL = os.environ['LAYMAN_TIMGEN_URL']
LAYMAN_CLIENT_URL = os.environ['LAYMAN_CLIENT_URL']
LAYMAN_CLIENT_PUBLIC_URL = os.getenv('LAYMAN_CLIENT_PUBLIC_URL', None)
LAYMAN_SERVER_NAME = os.environ['LAYMAN_SERVER_NAME']
LAYMAN_PROXY_SERVER_NAME = os.environ['LAYMAN_PROXY_SERVER_NAME']

CSW_URL = os.getenv('CSW_URL', None)
CSW_PROXY_URL = os.getenv('CSW_PROXY_URL', None)
CSW_BASIC_AUTHN = None if ':' not in os.getenv('CSW_BASIC_AUTHN', '') else tuple(os.environ['CSW_BASIC_AUTHN'].split(':'))
CSW_RECORD_URL = os.getenv('CSW_RECORD_URL', None)

# # tuples like (version, revision)
MICKA_ACCEPTED_VERSIONS = [
    ('2020.010', '2020-03-04.01'),
]
