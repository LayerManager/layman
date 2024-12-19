import os
import shutil
from celery.utils.log import get_task_logger

import crs as crs_def
from geoserver import util as gs_util
from layman.celery import AbortedException
from layman import celery_app, settings, util as layman_util
from layman.common import empty_method_returns_true, bbox as bbox_util
from layman.common.micka import util as micka_util
from layman.http import LaymanError
from . import wms, wfs, sld
from .. import geoserver, LAYER_TYPE

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
def refresh_wms(
        self,
        workspace,
        layername,
        store_in_geoserver,
        description=None,
        title=None,
        access_rights=None,
        image_mosaic=False,
        slugified_time_regex=None,
        slugified_time_regex_format=None,
        original_data_source=settings.EnumOriginalDataSource.FILE.value,
):
    info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': [
        'file', 'geodata_type', 'native_bounding_box', 'native_crs', 'table_uri', 'uuid'
    ]})
    geodata_type = info['geodata_type']
    crs = info['native_crs']

    assert title is not None
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    geoserver.ensure_workspace(workspace)
    metadata_url = micka_util.get_metadata_url(info['uuid'], url_type=micka_util.RecordUrlType.XML)

    if self.is_aborted():
        raise AbortedException

    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        if store_in_geoserver:
            table_uri = info['_table_uri']
            table_name = table_uri.table
            store_name = None
            if original_data_source == settings.EnumOriginalDataSource.TABLE.value:
                store_name = geoserver.create_external_db_store(workspace=geoserver_workspace,
                                                                layer=layername,
                                                                table_uri=table_uri,
                                                                )
            geoserver.publish_layer_from_db(workspace,
                                            layername,
                                            description,
                                            title,
                                            crs=crs,
                                            table_name=table_name,
                                            metadata_url=metadata_url,
                                            geoserver_workspace=geoserver_workspace,
                                            store_name=store_name,
                                            )
        else:
            geoserver.publish_layer_from_qgis(workspace,
                                              layername,
                                              description,
                                              title,
                                              metadata_url=metadata_url,
                                              geoserver_workspace=geoserver_workspace,
                                              )
    elif geodata_type == settings.GEODATA_TYPE_RASTER:
        file_paths = next(iter(info['_file']['paths'].values()))
        gs_file_path = file_paths['normalized_geoserver']
        real_bbox = info['native_bounding_box']
        bbox = bbox_util.ensure_bbox_with_area(real_bbox, crs_def.CRSDefinitions[crs].no_area_bbox_padding) \
            if not bbox_util.is_empty(real_bbox) else crs_def.CRSDefinitions[crs].default_bbox
        lat_lon_bbox = bbox_util.transform(bbox, crs, crs_def.EPSG_4326)
        if not image_mosaic:
            coverage_store_name = wms.get_geotiff_store_name(layername)
            coverage_type = gs_util.COVERAGESTORE_GEOTIFF
            enable_time_dimension = False
            source_file_or_dir = gs_file_path
        else:
            coverage_store_name = wms.get_image_mosaic_store_name(layername)
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
        gs_util.create_coverage_store(geoserver_workspace, settings.LAYMAN_GS_AUTH, coverage_store_name, source_file_or_dir, coverage_type=coverage_type)
        gs_util.publish_coverage(geoserver_workspace, settings.LAYMAN_GS_AUTH, coverage_store_name, layername, title,
                                 description, bbox, crs, lat_lon_bbox=lat_lon_bbox, metadata_url=metadata_url, enable_time_dimension=enable_time_dimension)
    else:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")

    geoserver.set_security_rules(workspace, layername, access_rights, settings.LAYMAN_GS_AUTH, geoserver_workspace)

    wms.clear_cache(workspace)

    try:
        wms_info = wms.get_layer_info(workspace=workspace,
                                      layername=layername)
    except BaseException:
        wms_info = {}

    if 'wms' not in wms_info:
        wms.delete_layer(workspace, layername)
        raise LaymanError(53,)

    if self.is_aborted():
        wms.delete_layer(workspace, layername)
        raise AbortedException


@celery_app.task(
    name='layman.layer.geoserver.wfs.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_wfs(
        self,
        workspace,
        layername,
        description=None,
        title=None,
        access_rights=None,
        original_data_source=settings.EnumOriginalDataSource.FILE.value,
):
    info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['geodata_type', 'native_crs', 'table_uri', 'uuid']})
    geodata_type = info['geodata_type']
    if geodata_type == settings.GEODATA_TYPE_RASTER:
        return
    if geodata_type != settings.GEODATA_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")

    assert title is not None
    geoserver.ensure_workspace(workspace)

    if self.is_aborted():
        raise AbortedException
    crs = info['native_crs']
    table_name = info['_table_uri'].table
    store_name = None
    if original_data_source == settings.EnumOriginalDataSource.TABLE.value:
        table_uri = info['_table_uri']
        store_name = geoserver.create_external_db_store(workspace=workspace,
                                                        layer=layername,
                                                        table_uri=table_uri,
                                                        )
    metadata_url = micka_util.get_metadata_url(info['uuid'], url_type=micka_util.RecordUrlType.XML)
    geoserver.publish_layer_from_db(workspace, layername, description, title, crs=crs, table_name=table_name, metadata_url=metadata_url, store_name=store_name)
    geoserver.set_security_rules(workspace, layername, access_rights, settings.LAYMAN_GS_AUTH, workspace)
    wfs.clear_cache(workspace)

    try:
        wfs_info = wfs.get_layer_info(workspace=workspace,
                                      layername=layername)
    except BaseException:
        wfs_info = {}

    if 'wfs' not in wfs_info:
        wfs.delete_layer(workspace, layername)
        raise LaymanError(53,)

    if self.is_aborted():
        wfs.delete_layer(workspace, layername)
        raise AbortedException


@celery_app.task(
    name='layman.layer.geoserver.sld.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_sld(self, workspace, layername, store_in_geoserver):
    if self.is_aborted():
        raise AbortedException
    if store_in_geoserver:
        sld.ensure_custom_sld_file_if_needed(workspace, layername)
        sld.create_layer_style(workspace, layername)

    if self.is_aborted():
        sld.delete_layer(workspace, layername)
        raise AbortedException
