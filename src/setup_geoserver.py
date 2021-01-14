import importlib
import logging
import os
import sys

import geoserver
from geoserver import epsg_properties
from geoserver import authn

settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])


logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def main():
    geoserver.ensure_data_dir(settings.GEOSERVER_DATADIR,
                              settings.GEOSERVER_INITIAL_DATADIR)
    authn.setup_authn(settings.GEOSERVER_DATADIR,
                      settings.LAYMAN_GS_AUTHN_FILTER_NAME,
                      settings.LAYMAN_GS_AUTHN_HTTP_HEADER_NAME,
                      settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE,
                      settings.LAYMAN_GS_USER_GROUP_SERVICE,
                      settings.LAYMAN_GS_ROLE_SERVICE,
                      settings.LAYMAN_GS_AUTHN_FILTER_NAME_OLD,
                      )
    epsg_properties.setup_epsg(settings.GEOSERVER_DATADIR,
                               set(settings.LAYMAN_OUTPUT_SRS_LIST))


if __name__ == "__main__":
    main()
