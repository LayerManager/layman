from . import util, wms
from layman import util as layman_util, settings


def ensure_output_srs_for_all():
    layers = layman_util.get_publication_infos(style_type='qgis')
    if layers:
        (workspace, _, layer) = next(iter(layers.keys()))
        if util.get_layer_wms_crs_list_values(workspace, layer) != settings.LAYMAN_OUTPUT_SRS_LIST:
            for (workspace, _, layer) in layers.keys():
                wms.save_qgs_file(workspace, layer)
