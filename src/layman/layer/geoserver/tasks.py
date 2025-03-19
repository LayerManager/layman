import os
import shutil
from celery.utils.log import get_task_logger

import crs as crs_def
from geoserver import util as gs_util
from layman.celery import AbortedException
from layman import celery_app, settings, util as layman_util
from layman.common import empty_method_returns_true, bbox as bbox_util
from layman.common.micka import util as micka_util
from . import wms, wfs, sld
from .util import DEFAULT_INTERNAL_DB_STORE, create_external_db_store, publish_layer_from_db, publish_layer_from_qgis, set_security_rules
from ..layer_class import Layer

logger = get_task_logger(__name__)
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


refresh_wms_needed = empty_method_returns_true
refresh_wfs_needed = empty_method_returns_true
refresh_sld_needed = empty_method_returns_true


@celery_app.task(
    name='layman.layer.geoserver.wms.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
# pylint: disable=unused-argument
def refresh_wms(
        self,
        workspace,
        layername,
        *,
        uuid,
        store_in_geoserver,
        access_rights=None,
        image_mosaic=False,
        slugified_time_regex=None,
        slugified_time_regex_format=None,
):
    layer = Layer(uuid=uuid)
    gs_layername = layer.gs_names.wms
    info = layman_util.get_publication_info_by_class(layer, context={'keys': ['file']})

    assert layer.title is not None
    metadata_url = micka_util.get_metadata_url(layer.uuid, url_type=micka_util.RecordUrlType.XML)

    if self.is_aborted():
        raise AbortedException

    if layer.geodata_type == settings.GEODATA_TYPE_VECTOR:
        if store_in_geoserver:
            if layer.original_data_source == settings.EnumOriginalDataSource.TABLE:
                store_name = create_external_db_store(workspace=gs_layername.workspace,
                                                      uuid=uuid,
                                                      table_uri=layer.table_uri,
                                                      )
            else:
                store_name = DEFAULT_INTERNAL_DB_STORE
            publish_layer_from_db(layer=layer,
                                  gs_names=gs_layername,
                                  metadata_url=metadata_url,
                                  store_name=store_name)
        else:
            publish_layer_from_qgis(layer=layer,
                                    gs_names=gs_layername,
                                    metadata_url=metadata_url,
                                    )
    elif layer.geodata_type == settings.GEODATA_TYPE_RASTER:
        file_paths = next(iter(info['_file']['paths'].values()))
        gs_file_path = file_paths['normalized_geoserver']
        bbox = bbox_util.get_bbox_to_publish(layer.native_bounding_box, layer.native_crs)
        lat_lon_bbox = bbox_util.transform(bbox, layer.native_crs, crs_def.EPSG_4326)
        if not image_mosaic:
            coverage_store_name = wms.get_geotiff_store_name(uuid=layer.uuid)
            coverage_type = gs_util.COVERAGESTORE_GEOTIFF
            enable_time_dimension = False
            source_file_or_dir = gs_file_path
        else:
            coverage_store_name = wms.get_image_mosaic_store_name(uuid=layer.uuid)
            source_file_or_dir = os.path.dirname(gs_file_path)
            file_path = file_paths['normalized_absolute']
            dir_path = os.path.dirname(file_path)
            shutil.copy(os.path.join(DIRECTORY, 'indexer.properties'), dir_path)
            timeregex_path = os.path.join(dir_path, 'timeregex.properties')
            timeregex_format_str = f',format={slugified_time_regex_format}' if slugified_time_regex_format else ''
            with open(timeregex_path, 'w', encoding="utf-8") as file:
                file.write(f'regex={slugified_time_regex}{timeregex_format_str}\n')
            coverage_type = gs_util.COVERAGESTORE_IMAGEMOSAIC
            enable_time_dimension = True
        gs_util.create_coverage_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, coverage_store_name, source_file_or_dir, coverage_type=coverage_type)
        gs_util.publish_coverage(gs_layername.workspace, settings.LAYMAN_GS_AUTH, coverage_store_name, gs_layername.name, layer.title,
                                 layer.description, bbox, layer.native_crs, lat_lon_bbox=lat_lon_bbox, metadata_url=metadata_url, enable_time_dimension=enable_time_dimension)
    else:
        raise NotImplementedError(f"Unknown geodata type: {layer.geodata_type}")

    set_security_rules(layer=layer,
                       gs_names=gs_layername,
                       access_rights=access_rights,
                       auth=settings.LAYMAN_GS_AUTH,
                       )

    wms.clear_cache()

    if self.is_aborted():
        wms.delete_layer(layer=layer)
        raise AbortedException


@celery_app.task(
    name='layman.layer.geoserver.wfs.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
# pylint: disable=unused-argument
def refresh_wfs(
        self,
        workspace,
        layername,
        *,
        uuid,
        access_rights=None,
        original_data_source=settings.EnumOriginalDataSource.FILE.value,
):
    layer = Layer(uuid=uuid)
    gs_layername = layer.gs_names.wfs
    if layer.geodata_type == settings.GEODATA_TYPE_RASTER:
        return
    if layer.geodata_type != settings.GEODATA_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown geodata type: {layer.geodata_type}")

    assert layer.title is not None

    if self.is_aborted():
        raise AbortedException
    if original_data_source == settings.EnumOriginalDataSource.TABLE.value:
        store_name = create_external_db_store(workspace=gs_layername.workspace,
                                              uuid=uuid,
                                              table_uri=layer.table_uri,
                                              )
    else:
        store_name = DEFAULT_INTERNAL_DB_STORE
    metadata_url = micka_util.get_metadata_url(uuid, url_type=micka_util.RecordUrlType.XML)
    publish_layer_from_db(layer=layer,
                          gs_names=gs_layername,
                          metadata_url=metadata_url,
                          store_name=store_name)
    set_security_rules(layer=layer,
                       gs_names=gs_layername,
                       access_rights=access_rights,
                       auth=settings.LAYMAN_GS_AUTH,
                       )
    wfs.clear_cache()

    if self.is_aborted():
        wfs.delete_layer(layer=layer)
        raise AbortedException


@celery_app.task(
    name='layman.layer.geoserver.sld.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
# pylint: disable=unused-argument
def refresh_sld(self, workspace, layername, store_in_geoserver, *, uuid):
    if self.is_aborted():
        raise AbortedException
    layer = Layer(uuid=uuid)
    if store_in_geoserver:
        sld.ensure_custom_sld_file_if_needed(layer=layer)
        sld.create_layer_style(layer=layer)

    if self.is_aborted():
        sld.delete_layer(layer=layer)
        raise AbortedException
