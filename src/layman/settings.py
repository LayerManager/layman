import os

LAYMAN_DATA_PATH = os.path.join(os.environ['GEOSERVER_DATA_DIR'],
                                os.environ['LAYMAN_DATA_DIR'])

TESTING = 'TESTING' in os.environ and os.environ['TESTING']=='True'

MAIN_FILE_EXTENSIONS = ['.geojson']

INPUT_SRS_LIST = [
    'EPSG:3857',
    'EPSG:4326',
]

PG_CONN = "host='{}' port='{}' dbname='{}' user='{}' password='{}'".format(
    os.environ['LAYMAN_PG_HOST'],
    os.environ['LAYMAN_PG_PORT'],
    os.environ['LAYMAN_PG_DBNAME'],
    os.environ['LAYMAN_PG_USER'],
    os.environ['LAYMAN_PG_PASSWORD'],
)

PG_NON_USER_SCHEMAS = [
    'public',
    'topology',
    'pg_catalog',
    'pg_toast',
    'information_schema',
]

PG_POSTGIS_SCHEMA = 'public'

