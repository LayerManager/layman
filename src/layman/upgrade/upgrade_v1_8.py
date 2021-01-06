from urllib.parse import urljoin
import logging
import requests

from layman import app, settings
from layman.common import geoserver
from layman.common.prime_db_schema import schema_initialization
from layman.layer.util import get_layer_infos

logger = logging.getLogger(__name__)


def older_than_1_8():
    return not schema_initialization.schema_exists()


def upgrade_1_8():
    logger.info(f'Upgrade to version 1.8.x')
    with app.app_context():
        logger.info(f'  Creating prime_db_schema')
        schema_initialization.check_schema_name(settings.LAYMAN_PRIME_SCHEMA)
        schema_initialization.ensure_schema(settings.LAYMAN_PRIME_SCHEMA,
                                            settings.PUBLICATION_MODULES,
                                            settings.RIGHTS_EVERYONE_ROLE)

        logger.info(f'  Ensuring users')
        from ..util import get_usernames, ensure_whole_user, check_username
        all_usernames = get_usernames()
        for username in all_usernames:
            logger.info(f'    Ensuring user {username}')
            check_username(username)
            ensure_whole_user(username)

        logger.info(f'  Ensuring GS rules')
        # Delete old rules for workspaces
        for username in all_usernames:
            headers_json = {
                'Accept': 'application/json',
                'Content-type': 'application/json',
            }

            for type in ['w', 'r']:
                r = requests.delete(
                    urljoin(settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS, username + '.*.' + type),
                    headers=headers_json,
                    auth=settings.LAYMAN_GS_AUTH
                )
                if r.status_code != 404:
                    r.raise_for_status()

        # Create rules for publications/layers
        for username in all_usernames:
            logger.info(f'    Ensuring GS rules for user {username}')
            for layer, info in get_layer_infos(username).items():
                logger.info(f'      Ensuring GS rules for user {username} and layer {layer}')
                for type in ['read', 'write']:
                    security_read_roles = geoserver.layman_users_to_geoserver_roles(info['access_rights'][type])
                    geoserver.ensure_layer_security_roles(username, layer, security_read_roles, type[0], settings.LAYMAN_GS_AUTH)
