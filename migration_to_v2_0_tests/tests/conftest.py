import geoserver
import layman_settings as settings

geoserver.set_settings(f"http://localhost:8600/geoserver/", settings.LAYMAN_GS_ROLE_SERVICE,
                       settings.LAYMAN_GS_USER_GROUP_SERVICE, settings.DEFAULT_CONNECTION_TIMEOUT)
