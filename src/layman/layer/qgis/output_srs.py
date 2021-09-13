import os
import logging
from layman import util as layman_util, settings
from . import util, wms

logger = logging.getLogger(__name__)


def ensure_output_srs_for_all():
    qml_layers = layman_util.get_publication_infos(style_type='qml')
    first_layer_with_qgis_file = next((
        (workspace, layer) for (workspace, _, layer) in iter(qml_layers.keys())
        if os.path.exists(wms.get_layer_file_path(workspace, layer))
    ), None)
    if first_layer_with_qgis_file is not None:
        workspace, layer = first_layer_with_qgis_file
        old_set = util.get_layer_wms_crs_list_values(workspace, layer)
        if old_set != set(settings.LAYMAN_OUTPUT_SRS_LIST):
            logger.info(f'  Update output SRS list for QGIS projects. Old set={old_set},'
                        f' new list={settings.LAYMAN_OUTPUT_SRS_LIST}')
            for (workspace, _, layer) in qml_layers.keys():
                try:
                    wms.save_qgs_file(workspace, layer)
                except BaseException as exc:
                    logger.warning(f"    SRS list of layer {workspace}.{layer} not updated"
                                   f" because of following exception:")
                    logger.exception(exc)
