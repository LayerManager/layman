import logging
from layman import util as layman_util, settings
from . import util, wms

logger = logging.getLogger(__name__)


def ensure_output_srs_for_all():
    layers = layman_util.get_publication_infos(style_type='qml')
    if layers:
        (workspace, _, layer) = next(iter(layers.keys()))
        old_set = util.get_layer_wms_crs_list_values(workspace, layer)
        if old_set != set(settings.LAYMAN_OUTPUT_SRS_LIST):
            logger.info(f'  Update output SRS list for QGIS projects. Old set={old_set}, new list={settings.LAYMAN_OUTPUT_SRS_LIST}')
            for (workspace, _, layer) in layers.keys():
                wms.save_qgs_file(workspace, layer)
