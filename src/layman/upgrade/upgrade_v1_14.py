import logging

from db import util as db_util
from geoserver import util as gs_util
from layman import settings, util as layman_util
from layman.layer import LAYER_TYPE, geoserver, util as layer_util
from layman.layer.geoserver import wfs as gs_wfs, wms as gs_wms
from layman.layer.filesystem import thumbnail as layer_thumbnail
from layman.layer.micka import soap as layer_micka_soap
from layman.layer.qgis import wms as qgis_wms
from layman.map import MAP_TYPE
from layman.map.micka import soap as map_micka_soap

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def crop_bbox():
    logger.info(f'    Crop bounding boxes')
    query = f'''select w.name,
    p.type,
    p.name,
    ST_XMIN(p.bbox) as xmin,
    ST_YMIN(p.bbox) as ymin,
    ST_XMAX(p.bbox) as xmax,
    ST_YMAX(p.bbox) as ymax
from {DB_SCHEMA}.publications p inner join
     {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
where st_xMin(p.bbox) < -20026376.39
   or st_yMin(p.bbox) < -20048966.10
   or st_xMax(p.bbox) > 20026376.39
   or st_yMax(p.bbox) > 20048966.10
;'''
    publications = db_util.run_query(query, settings.LAYMAN_DEFAULT_OUTPUT_BBOX)
    for workspace, publ_type, publication, xmin, ymin, xmax, ymax in publications:
        info = layman_util.get_publication_info(workspace, publ_type, publication, context={'keys': ['style_type', 'file', 'uuid'], })

        original_bbox = (xmin, ymin, xmax, ymax)
        cropped_bbox = (
            max(original_bbox[0], settings.LAYMAN_DEFAULT_OUTPUT_BBOX[0]),
            max(original_bbox[1], settings.LAYMAN_DEFAULT_OUTPUT_BBOX[1]),
            min(original_bbox[2], settings.LAYMAN_DEFAULT_OUTPUT_BBOX[2]),
            min(original_bbox[3], settings.LAYMAN_DEFAULT_OUTPUT_BBOX[3]),
        )
        query = f'''update {DB_SCHEMA}.publications set
        bbox = ST_MakeBox2D(ST_Point(%s, %s), ST_Point(%s ,%s))
        where type = %s
          and name = %s
          and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
        params = cropped_bbox + (publ_type, publication, workspace,)
        db_util.run_statement(query, params)

        if publ_type == LAYER_TYPE:
            file_type = info['file']['file_type']
            assert file_type == settings.FILE_TYPE_VECTOR

            #  WFS
            bbox = geoserver.get_layer_bbox(workspace, publication)
            gs_util.patch_feature_type(workspace, publication, auth=settings.LAYMAN_GS_AUTH, bbox=bbox)
            gs_wfs.clear_cache(workspace)

            #  WMS
            style_type = info['style_type']
            geoserver_workspace = gs_wms.get_geoserver_workspace(workspace)
            if style_type == 'sld':
                gs_util.patch_feature_type(geoserver_workspace, publication, auth=settings.LAYMAN_GS_AUTH, bbox=bbox)
            elif style_type == 'qml':
                qgis_wms.save_qgs_file(workspace, publication)
                gs_util.patch_wms_layer(geoserver_workspace, publication, auth=settings.LAYMAN_GS_AUTH, bbox=bbox)
            gs_wms.clear_cache(workspace)

            # Thumbnail
            layer_thumbnail.generate_layer_thumbnail(workspace, publication)

            # Micka soap
            layer_micka_soap.patch_layer(workspace, publication, metadata_properties_to_refresh=['extent'])

            md_props = layer_util.get_metadata_comparison(workspace, publication, cached=False)
            assert md_props['metadata_properties']['extent']['equal'], f'{md_props}'
        elif publ_type == MAP_TYPE:
            # Micka soap
            map_micka_soap.patch_map(workspace, publication, metadata_properties_to_refresh=['extent'])
