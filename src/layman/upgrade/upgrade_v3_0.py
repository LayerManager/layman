import logging
import traceback
from db import util as db_util
from layman import app, util as layman_util, settings
from layman.map import MAP_TYPE
from layman.layer import LAYER_TYPE
from layman.map.micka import csw
from layman.layer.micka import csw as layer_csw
from layman.map.map_class import Map
from layman.layer.layer_class import Layer

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_file_path():
    logger.info(f'    Alter DB prime schema for file_path')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS file_path text;'''
    db_util.run_statement(statement)

    statement = f'''
    DO $$ BEGIN
        ALTER TABLE {DB_SCHEMA}.publications ADD CONSTRAINT file_path_with_geodata_type_check
            CHECK (file_path IS NULL OR geodata_type = '{settings.GEODATA_TYPE_RASTER}');
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;'''
    db_util.run_statement(statement)


def migrate_metadata_urls(publ_type):
    type_name = 'map' if publ_type == MAP_TYPE else 'layer'
    logger.info(f'Starting Micka {type_name} graphic URL migration to v3.0 format.')

    with app.app_context():
        publications = layman_util.get_publication_infos(publ_type=publ_type)

    for (workspace, _, pubname), pub_info in publications.items():
        uuid = pub_info['uuid']
        try:
            if publ_type == MAP_TYPE:
                publication = Map(uuid=uuid)
                csw.patch_map(
                    publication=publication,
                    metadata_properties_to_refresh=['graphic_url', 'map_file_endpoint'],
                    actor_name=workspace,
                    create_if_not_exists=False
                )
            elif publ_type == LAYER_TYPE:
                publication = Layer(uuid=uuid)
                layer_csw.patch_layer(
                    publication=publication,
                    metadata_properties_to_refresh=['graphic_url'],
                    actor_name=workspace,
                    create_if_not_exists=False
                )
        except BaseException:
            logger.error(f"Error migrating graphic_url for {type_name} {workspace}:{pubname}, error: {traceback.format_exc()}")
            continue

    logger.info(f'{type_name.capitalize()} graphic URL migration to v3.0 format completed.')


def migrate_map_metadata_urls():
    migrate_metadata_urls(MAP_TYPE)


def migrate_layer_metadata_urls():
    migrate_metadata_urls(LAYER_TYPE)
