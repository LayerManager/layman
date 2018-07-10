import os

LAYMAN_DATA_PATH = os.path.join(os.environ['GEOSERVER_DATA_DIR'],
                                os.environ['LAYMAN_DATA_DIR'])

TESTING = 'TESTING' in os.environ and os.environ['TESTING']=='True'

MAIN_FILE_EXTENSIONS = ['.geojson']