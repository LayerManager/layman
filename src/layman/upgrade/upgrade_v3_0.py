import logging
import traceback
from layman import app, util as layman_util
from layman.map import MAP_TYPE
from layman.map.micka import csw
from layman.map.map_class import Map

logger = logging.getLogger(__name__)


def migrate_graphic_urls():
    logger.info('Starting Micka graphic URL migration to v3.0 format.')

    with app.app_context():
        maps = layman_util.get_publication_infos(publ_type=MAP_TYPE)
    for (workspace, _, mapname), map_info in maps.items():
        uuid = map_info['uuid']
        try:
            publication = Map(uuid=uuid)
            csw.patch_map(
                publication=publication,
                metadata_properties_to_refresh=['graphic_url'],
                actor_name=workspace,
                create_if_not_exists=False
            )
        except BaseException:
            logger.error(f"Error migrating graphic_url for {workspace}:{mapname}, error: {traceback.format_exc()}")
            continue

    logger.info('Graphic URL migration to v3.0 format completed.')
