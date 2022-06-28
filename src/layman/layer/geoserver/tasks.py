from celery.utils.log import get_task_logger

import crs as crs_def
from geoserver import util as gs_util
from layman.celery import AbortedException
from layman import celery_app, settings, util as layman_util
from layman.common import empty_method_returns_true, bbox as bbox_util
from . import wms, wfs, sld
from .. import geoserver, LAYER_TYPE

logger = get_task_logger(__name__)


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
):
    info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['file', 'native_bounding_box', 'native_crs', 'db_table']})
    file_type = info['file']['file_type']
    crs = info['native_crs']

    assert description is not None
    assert title is not None
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    geoserver.ensure_workspace(workspace)

    if self.is_aborted():
        raise AbortedException

    coverage_store_name = wms.get_geotiff_store_name(layername)
    if file_type == settings.FILE_TYPE_VECTOR:
        if store_in_geoserver:
            gs_util.delete_wms_layer(geoserver_workspace, layername, settings.LAYMAN_GS_AUTH)
            gs_util.delete_wms_store(geoserver_workspace, settings.LAYMAN_GS_AUTH, wms.get_qgis_store_name(layername))
            table_name = info['db_table']['name']
            geoserver.publish_layer_from_db(workspace,
                                            layername,
                                            description,
                                            title,
                                            crs=crs,
                                            table_name=table_name,
                                            geoserver_workspace=geoserver_workspace,
                                            )
        else:
            gs_util.delete_feature_type(geoserver_workspace, layername, settings.LAYMAN_GS_AUTH)
            geoserver.publish_layer_from_qgis(workspace,
                                              layername,
                                              description,
                                              title,
                                              geoserver_workspace=geoserver_workspace,
                                              )
    elif file_type == settings.FILE_TYPE_RASTER:
        file_path = info['_file']['normalized_file']['gs_path']
        real_bbox = info['native_bounding_box']
        bbox = bbox_util.ensure_bbox_with_area(real_bbox, crs_def.CRSDefinitions[crs].no_area_bbox_padding)\
            if not bbox_util.is_empty(real_bbox) else crs_def.CRSDefinitions[crs].default_bbox
        lat_lon_bbox = bbox_util.transform(bbox, crs, crs_def.EPSG_4326)
        gs_util.create_coverage_store(geoserver_workspace, settings.LAYMAN_GS_AUTH, coverage_store_name, file_path)
        gs_util.publish_coverage(geoserver_workspace, settings.LAYMAN_GS_AUTH, coverage_store_name, layername, title,
                                 description, bbox, crs, lat_lon_bbox=lat_lon_bbox)
    else:
        raise NotImplementedError(f"Unknown file type: {file_type}")

    geoserver.set_security_rules(workspace, layername, access_rights, settings.LAYMAN_GS_AUTH, geoserver_workspace)

    wms.clear_cache(workspace)

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
):
    info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['file', 'native_crs', 'db_table', ]})
    file_type = info['file']['file_type']
    if file_type == settings.FILE_TYPE_RASTER:
        return
    if file_type != settings.FILE_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown file type: {file_type}")

    assert description is not None
    assert title is not None
    geoserver.ensure_workspace(workspace)

    if self.is_aborted():
        raise AbortedException
    crs = info['native_crs']
    table_name = info['db_table']['name']
    geoserver.publish_layer_from_db(workspace, layername, description, title, crs=crs, table_name=table_name, )
    geoserver.set_security_rules(workspace, layername, access_rights, settings.LAYMAN_GS_AUTH, workspace)
    wfs.clear_cache(workspace)

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
        sld.create_layer_style(workspace, layername)

    if self.is_aborted():
        sld.delete_layer(workspace, layername)
        raise AbortedException
