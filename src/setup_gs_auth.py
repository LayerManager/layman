import importlib
import logging
import os
import sys

from geoserver import authn as gs_authn

settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])


logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

ATTEMPT_INTERVAL = 2
MAX_ATTEMPTS = 60


def main():
    gs_authn.ensure_data_dir(settings.GEOSERVER_DATADIR, settings.GEOSERVER_INITIAL_DATADIR)

    gs_authn.ensure_request_header_authn(
        settings.GEOSERVER_DATADIR,
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_NAME,
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE,
        settings.LAYMAN_GS_USER_GROUP_SERVICE,
        settings.LAYMAN_GS_ROLE_SERVICE
    )

    gs_authn.remove_security_filter_groups(
        settings.GEOSERVER_DATADIR,
        settings.LAYMAN_GS_AUTHN_FILTER_NAME_OLD,
    )

    gs_authn.ensure_security_filter_group(
        settings.GEOSERVER_DATADIR,
        settings.LAYMAN_GS_AUTHN_FILTER_NAME,
        [
            settings.LAYMAN_GS_AUTHN_HTTP_HEADER_NAME,
            'basic',
            'anonymous',
        ]
    )


if __name__ == "__main__":
    main()
