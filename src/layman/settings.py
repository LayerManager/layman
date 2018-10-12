import os
from urllib.parse import urljoin

LAYMAN_DATA_PATH = os.path.join(os.environ['GEOSERVER_DATA_DIR'],
                                os.environ['LAYMAN_DATA_DIR'])

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

PG_CONN = "host='{}' port='{}' dbname='{}' user='{}' password='{}'".format(
    LAYMAN_PG_HOST,
    LAYMAN_PG_PORT,
    LAYMAN_PG_DBNAME,
    LAYMAN_PG_USER,
    LAYMAN_PG_PASSWORD,
)

LAYMAN_GS_AUTH = (os.environ['LAYMAN_GS_USER'],
                  os.environ['LAYMAN_GS_PASSWORD'])

LAYMAN_GS_HOST = os.environ['LAYMAN_GS_HOST']
LAYMAN_GS_PORT = os.environ['LAYMAN_GS_PORT']
LAYMAN_GS_PATH = os.environ['LAYMAN_GS_PATH']

LAYMAN_GS_URL = "http://{}:{}{}".format(
    LAYMAN_GS_HOST,
    LAYMAN_GS_PORT,
    LAYMAN_GS_PATH,
)

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

from layman.geoserver.util import get_gs_proxy_base_url
LAYMAN_GS_PROXY_URL = get_gs_proxy_base_url()

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

PG_CONN_TEMPLATE = "host='{}' port='{}' dbname='{}' user='{}' password='{" \
               "}'".format(
    os.environ['LAYMAN_PG_HOST'],
    os.environ['LAYMAN_PG_PORT'],
    LAYMAN_PG_TEMPLATE_DBNAME,
    os.environ['LAYMAN_PG_USER'],
    os.environ['LAYMAN_PG_PASSWORD'],
)

LAYMAN_CELERY_QUEUE = os.environ['LAYMAN_CELERY_QUEUE']


SOURCES = [
    'layman.filesystem.input_files',
    'layman.filesystem.input_sld',
    'layman.db.table',
    'layman.geoserver.wfs',
    'layman.geoserver.wms',
    'layman.geoserver.sld',
    'layman.filesystem.thumbnail',
]