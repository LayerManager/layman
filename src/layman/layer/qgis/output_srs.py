import os
import logging
from layman import util as layman_util, settings
from . import util, wms

logger = logging.getLogger(__name__)


def ensure_output_srs_for_all():
    qml_layers = layman_util.get_publication_infos(style_type='qml')
    first_layer_with_qgis_file_uuid = next((
        info['uuid'] for info in qml_layers.values()
        if os.path.exists(wms.get_layer_file_path(info['uuid']))
    ), None)
    if first_layer_with_qgis_file_uuid is not None:
        old_set = util.get_layer_wms_crs_list_values(first_layer_with_qgis_file_uuid)
        if old_set != set(settings.LAYMAN_OUTPUT_SRS_LIST):
            logger.info(f'  Update output SRS list for QGIS projects. Old set={old_set},'
                        f' new list={settings.LAYMAN_OUTPUT_SRS_LIST}')
            for info in qml_layers.values():
                try:
                    wms.save_qgs_file(info['uuid'])
                except BaseException as exc:
                    logger.warning(f"    SRS list of layer {info['uuid']} not updated"
                                   f" because of following exception:")
                    logger.exception(exc)
