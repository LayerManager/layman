import logging
import traceback
from layman import app, util as layman_util
from layman.map import MAP_TYPE
from layman.map.micka.tasks import refresh_soap
from layman.common import REQUEST_METHOD_PATCH
from layman.upgrade import upgrade_v2_0_util as util

logger = logging.getLogger(__name__)


def migrate_graphic_urls():
    with app.app_context():
        maps = layman_util.get_publication_infos(publ_type=MAP_TYPE)
    for workspace, publication_type, mapname in maps:
        uuid = layman_util.get_publication_uuid(workspace, publication_type, mapname)
        try:
            kwargs = {
                'http_method': REQUEST_METHOD_PATCH,
                'metadata_properties_to_refresh': ['graphic_url'],
                'uuid': uuid,
                'actor_name': workspace
            }
            util.run_task_sync(refresh_soap, [workspace, mapname], kwargs)
        except BaseException:
            logger.error(f'    Fail to refresh metadata od Micka: \n{traceback.format_exc()}')

    logger.info('Graphic URL migration to v3.0 format completed')
