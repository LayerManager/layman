import os
import re
from urllib.parse import urljoin, urlparse
from enum import Enum
import redis

import db
import geoserver
from layman_settings_util import read_clients_dict_from_env


class EnumOriginalDataSource(Enum):
    FILE = 'file'
    TABLE = 'database_table'


LAYMAN_DATA_DIR = os.environ['LAYMAN_DATA_DIR']

FILE_TYPE_VECTOR = 'vector'
FILE_TYPE_RASTER = 'raster'
FILE_TYPE_UNKNOWN = 'unknown'

MAIN_FILE_EXTENSIONS = {
    '.geojson': FILE_TYPE_VECTOR,
    '.shp': FILE_TYPE_VECTOR,
    '.tiff': FILE_TYPE_RASTER,
    '.tif': FILE_TYPE_RASTER,
    '.jp2': FILE_TYPE_RASTER,
    '.png': FILE_TYPE_RASTER,
    '.jpg': FILE_TYPE_RASTER,
    '.jpeg': FILE_TYPE_RASTER,
}

# Files are opened with dedicated tools for each format, so adding new extension is not sufficient for new compress format to start working
COMPRESSED_FILE_EXTENSIONS = {
    '.zip': '/vsizip/',
}

ALLOWED_INPUT_SRS_LIST = [
    'EPSG:3857',
    'EPSG:4326',
    'EPSG:5514',
    'EPSG:32633',
    'EPSG:32634',
    'EPSG:3034',
    'EPSG:3035',
    'EPSG:3059',
]

INPUT_SRS_LIST = [
    f'EPSG:{int(code)}' for code in os.environ['LAYMAN_INPUT_SRS_LIST'].split(',')
    if len(code) > 0
]
for input_srs in INPUT_SRS_LIST:
    assert input_srs in ALLOWED_INPUT_SRS_LIST, f'Input CRS {input_srs} is not allowed.'
for mandatory_srs in ['EPSG:3857',
                      'EPSG:4326',
                      ]:
    if mandatory_srs not in INPUT_SRS_LIST:
        INPUT_SRS_LIST.append(mandatory_srs)

OVERVIEW_RESAMPLING_METHOD_LIST = [
    'nearest',
    'average',
    'rms',
    'bilinear',
    'gauss',
    'cubic',
    'cubicspline',
    'lanczos',
    'average_magphase',
    'mode',
]

DEFAULT_CONNECTION_TIMEOUT = int(os.environ['DEFAULT_CONNECTION_TIMEOUT'])

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
db.PG_CONN = PG_CONN
PG_URI_STR = f"postgresql://{LAYMAN_PG_USER}:{LAYMAN_PG_PASSWORD}@{LAYMAN_PG_HOST}:{LAYMAN_PG_PORT}/{LAYMAN_PG_DBNAME}"

GEOSERVER_ADMIN_USER = 'admin'
GEOSERVER_ADMIN_PASSWORD = os.getenv('GEOSERVER_ADMIN_PASSWORD', None)
GEOSERVER_ADMIN_AUTH = None if GEOSERVER_ADMIN_PASSWORD is None else (GEOSERVER_ADMIN_USER,
                                                                      GEOSERVER_ADMIN_PASSWORD)
GEOSERVER_DATADIR = '/geoserver/data_dir'
GEOSERVER_INITIAL_DATADIR = '/geoserver/initial_data_dir'
LAYMAN_GS_ROLE_SERVICE = os.getenv('LAYMAN_GS_ROLE_SERVICE', '') or 'default'
LAYMAN_GS_USER_GROUP_SERVICE = os.getenv('LAYMAN_GS_USER_GROUP_SERVICE', '') or 'default'

LAYMAN_GS_USER = os.environ['LAYMAN_GS_USER']
LAYMAN_GS_PASSWORD = os.environ['LAYMAN_GS_PASSWORD']
LAYMAN_GS_AUTH = (LAYMAN_GS_USER, LAYMAN_GS_PASSWORD)

LAYMAN_GS_HOST = os.environ['LAYMAN_GS_HOST']
LAYMAN_GS_PORT = os.environ['LAYMAN_GS_PORT']
LAYMAN_GS_PATH = os.environ['LAYMAN_GS_PATH']

LAYMAN_GS_URL = f"http://{LAYMAN_GS_HOST}:{LAYMAN_GS_PORT}{LAYMAN_GS_PATH}"
geoserver.set_settings(LAYMAN_GS_URL, LAYMAN_GS_ROLE_SERVICE, LAYMAN_GS_USER_GROUP_SERVICE, DEFAULT_CONNECTION_TIMEOUT, )
geoserver.GS_AUTH = LAYMAN_GS_AUTH

LAYMAN_GS_ROLE = os.environ['LAYMAN_GS_ROLE']

LAYMAN_GS_AUTHN_HTTP_HEADER_NAME = 'laymanHttpHeader'
LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE = os.environ['LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE']
assert re.match("[a-z][a-z0-9]*", LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE), "Only lowercase characters and numbers " \
                                                                          "should be used for " \
                                                                          "LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE. "
LAYMAN_GS_AUTHN_FILTER_NAME = 'laymanHttpFilter_v2'
LAYMAN_GS_AUTHN_FILTER_NAME_OLD = ['laymanHttpFilter']

LAYMAN_GS_WMS_WORKSPACE_POSTFIX = '_wms'

LAYMAN_OUTPUT_SRS_LIST = [
    f'EPSG:{int(code)}' for code in os.environ['LAYMAN_OUTPUT_SRS_LIST'].split(',')
    if len(code) > 0
]
for mandatory_srs in INPUT_SRS_LIST:
    if mandatory_srs not in LAYMAN_OUTPUT_SRS_LIST:
        LAYMAN_OUTPUT_SRS_LIST.append(mandatory_srs)


LAYMAN_QGIS_HOST = os.environ['LAYMAN_QGIS_HOST']
LAYMAN_QGIS_PORT = os.environ['LAYMAN_QGIS_PORT']
LAYMAN_QGIS_PATH = os.environ['LAYMAN_QGIS_PATH']

LAYMAN_QGIS_URL = f"http://{LAYMAN_QGIS_HOST}:{LAYMAN_QGIS_PORT}{LAYMAN_QGIS_PATH}"
LAYMAN_QGIS_DATA_DIR = os.environ['LAYMAN_QGIS_DATA_DIR']

LAYMAN_NORMALIZED_RASTER_DATA_DIR_NAME = os.environ['LAYMAN_GS_NORMALIZED_RASTER_DIRECTORY']
LAYMAN_NORMALIZED_RASTER_DATA_DIR = os.path.join(GEOSERVER_DATADIR, LAYMAN_NORMALIZED_RASTER_DATA_DIR_NAME)

# Name of schema, where Layman stores data about publication, users, ...
LAYMAN_PRIME_SCHEMA = os.environ['LAYMAN_PRIME_SCHEMA']
assert re.match("[a-z_][a-z0-9_]*", LAYMAN_PRIME_SCHEMA), "Only lowercase characters, numbers and underscore " \
                                                          "should be used for " \
                                                          "PG_PRIME_SCHEMA. "

# List of schemas that are not allowed to be used as usernames.
PG_NON_USER_SCHEMAS = [
    'public',
    'topology',
    'pg_catalog',
    'pg_toast',
    'information_schema',
    LAYMAN_PRIME_SCHEMA,
]

PG_POSTGIS_SCHEMA = 'public'

# Name of "everyone" role in rights
RIGHTS_EVERYONE_ROLE = "EVERYONE"
ANONYM_USER = "--ANONYM--"
NONAME_USER = "--NONAME--"

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
if 'layman.authn.http_header' not in LAYMAN_AUTHN_MODULES:
    LAYMAN_AUTHN_MODULES.append('layman.authn.http_header')

LAYMAN_AUTHN_HTTP_HEADER_NAME = os.environ['LAYMAN_AUTHN_HTTP_HEADER_NAME']
assert re.match("[a-z][a-z0-9]*", LAYMAN_AUTHN_HTTP_HEADER_NAME), "Only lowercase characters and numbers " \
    "should be used for " \
    "LAYMAN_AUTHN_HTTP_HEADER_NAME. "

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
OAUTH2_LIFERAY_INTROSPECTION_SUB_KEY = os.getenv('OAUTH2_LIFERAY_INTROSPECTION_SUB_KEY') or 'sub'
OAUTH2_LIFERAY_USER_PROFILE_URL = os.getenv('OAUTH2_LIFERAY_USER_PROFILE_URL', None)
OAUTH2_LIFERAY_CLIENTS = [
    d for d in read_clients_dict_from_env()
    if len(d['id']) > 0
]

GRANT_CREATE_PUBLIC_WORKSPACE = {
    name for name in os.environ['GRANT_CREATE_PUBLIC_WORKSPACE'].split(',')
    if name
}
GRANT_PUBLISH_IN_PUBLIC_WORKSPACE = {
    name for name in os.environ['GRANT_PUBLISH_IN_PUBLIC_WORKSPACE'].split(',')
    if name
}
if RIGHTS_EVERYONE_ROLE not in GRANT_PUBLISH_IN_PUBLIC_WORKSPACE:
    assert not GRANT_CREATE_PUBLIC_WORKSPACE.difference(GRANT_PUBLISH_IN_PUBLIC_WORKSPACE)

# UPLOAD_MAX_INACTIVITY_TIME = 10 # 10 seconds
UPLOAD_MAX_INACTIVITY_TIME = 5 * 60  # 5 minutes

# max time (in seconds) to cache GeoServer's requests like WMS capabilities
LAYMAN_CACHE_GS_TIMEOUT = 1 * 60  # 1 minute

LAYMAN_REDIS_URL = os.environ['LAYMAN_REDIS_URL']

LAYMAN_REDIS = redis.Redis.from_url(LAYMAN_REDIS_URL, encoding="utf-8", decode_responses=True)

LAYMAN_TIMGEN_URL = os.environ['LAYMAN_TIMGEN_URL']
LAYMAN_CLIENT_URL = os.environ['LAYMAN_CLIENT_URL']
LAYMAN_CLIENT_PUBLIC_URL = os.environ['LAYMAN_CLIENT_PUBLIC_URL']
LAYMAN_SERVER_NAME = os.environ['LAYMAN_SERVER_NAME']
LAYMAN_PROXY_SERVER_NAME = os.environ['LAYMAN_PROXY_SERVER_NAME']

LAYMAN_GS_PROXY_BASE_URL = os.getenv('LAYMAN_GS_PROXY_BASE_URL', urljoin(LAYMAN_CLIENT_PUBLIC_URL, LAYMAN_GS_PATH))

CSW_URL = os.getenv('CSW_URL', None)
CSW_PROXY_URL = os.getenv('CSW_PROXY_URL', None)
CSW_BASIC_AUTHN = None if ':' not in os.getenv('CSW_BASIC_AUTHN', '') else tuple(
    os.environ['CSW_BASIC_AUTHN'].split(':'))
CSW_RECORD_URL = os.getenv('CSW_RECORD_URL', None)

# # tuples like (version, revision)
MICKA_REGEXP = r"^(?P<operation>==|>=|)(?P<version>[0-9.]+):(?P<revision>[0-9-.]+)$"
MICKA_REGEXP_MATCH = re.search(MICKA_REGEXP, os.getenv('MICKA_ACCEPTED_VERSION', None) or '==2020.014:2020-04-15.01')
assert MICKA_REGEXP_MATCH, f'os.getenv(MICKA_ACCEPTED_VERSION)={os.getenv("MICKA_ACCEPTED_VERSION", "")}, MICKA_REGEXP_MATCH={MICKA_REGEXP_MATCH}'
assert len(
    MICKA_REGEXP_MATCH.groups()) == 3, f'os.getenv(MICKA_ACCEPTED_VERSION)={os.getenv("MICKA_ACCEPTED_VERSION", "")}, MICKA_REGEXP_MATCH={MICKA_REGEXP_MATCH}'
MICKA_ACCEPTED_VERSION = MICKA_REGEXP_MATCH.groups()

LAYMAN_PUBLIC_URL_SCHEME = urlparse(LAYMAN_CLIENT_PUBLIC_URL).scheme

REST_USERS_PREFIX = 'users'
REST_WORKSPACES_PREFIX = 'workspaces'
RESERVED_WORKSPACE_NAMES = {REST_USERS_PREFIX, REST_WORKSPACES_PREFIX}

# PREFERRED_LANGUAGES = ['cs', 'en']

OGR_DEFAULT_PRIMARY_KEY = 'ogc_fid'
OGR_DEFAULT_GEOMETRY_COLUMN = 'wkb_geometry'
