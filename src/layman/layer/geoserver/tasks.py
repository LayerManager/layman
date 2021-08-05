from celery.utils.log import get_task_logger

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
        username,
        layername,
        store_in_geoserver,
        description=None,
        title=None,
        ensure_user=False,
        access_rights=None,
):
    info = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['file', 'bounding_box']})
    file_type = info['file']['file_type']

    assert description is not None
    assert title is not None
    geoserver_workspace = wms.get_geoserver_workspace(username)
    if ensure_user:
        geoserver.ensure_workspace(username)

    if self.is_aborted():
        raise AbortedException

    coverage_store_name = wms.get_geotiff_store_name(layername)
    if file_type == settings.FILE_TYPE_VECTOR:
        if store_in_geoserver:
            gs_util.delete_wms_layer(geoserver_workspace, layername, settings.LAYMAN_GS_AUTH)
            gs_util.delete_wms_store(geoserver_workspace, settings.LAYMAN_GS_AUTH, wms.get_qgis_store_name(layername))
            geoserver.publish_layer_from_db(username,
                                            layername,
                                            description,
                                            title,
                                            geoserver_workspace=geoserver_workspace,
                                            )
        else:
            gs_util.delete_feature_type(geoserver_workspace, layername, settings.LAYMAN_GS_AUTH)
            geoserver.publish_layer_from_qgis(username,
                                              layername,
                                              description,
                                              title,
                                              geoserver_workspace=geoserver_workspace,
                                              )
    elif file_type == settings.FILE_TYPE_RASTER:
        file_path = info['_file']['normalized_file']['gs_path']
        real_bbox = info['bounding_box']
        bbox = bbox_util.ensure_bbox_with_area(real_bbox, settings.NO_AREA_BBOX_PADDING)\
            if not bbox_util.is_empty(real_bbox) else settings.LAYMAN_DEFAULT_OUTPUT_BBOX
        gs_util.create_coverage_store(geoserver_workspace, settings.LAYMAN_GS_AUTH, coverage_store_name, file_path)
        gs_util.publish_coverage(geoserver_workspace, settings.LAYMAN_GS_AUTH, coverage_store_name, layername, title, description, bbox)

    geoserver.set_security_rules(username, layername, access_rights, settings.LAYMAN_GS_AUTH, geoserver_workspace)

    wms.clear_cache(username)

    if self.is_aborted():
        wms.delete_layer(username, layername)
        raise AbortedException


@celery_app.task(
    name='layman.layer.geoserver.wfs.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_wfs(
        self,
        username,
        layername,
        description=None,
        title=None,
        ensure_user=False,
        access_rights=None,
):
    file_type = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['file']})['file']['file_type']
    if file_type != settings.FILE_TYPE_VECTOR:
        return

    assert description is not None
    assert title is not None
    if ensure_user:
        geoserver.ensure_workspace(username)

    if self.is_aborted():
        raise AbortedException
    geoserver.publish_layer_from_db(username, layername, description, title)
    geoserver.set_security_rules(username, layername, access_rights, settings.LAYMAN_GS_AUTH, username)
    wfs.clear_cache(username)

    if self.is_aborted():
        wfs.delete_layer(username, layername)
        raise AbortedException


@celery_app.task(
    name='layman.layer.geoserver.sld.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_sld(self, username, layername, store_in_geoserver):
    if self.is_aborted():
        raise AbortedException
    if store_in_geoserver:
        sld.create_layer_style(username, layername)

    if self.is_aborted():
        sld.delete_layer(username, layername)
        raise AbortedException
