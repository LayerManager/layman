import os
import shutil

from layman import patch_mode, settings
from layman.layer import qgis

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_publication_uuid(username, publication_type, publication_name):
    return None


def get_metadata_comparison(username, layername):
    pass


def pre_publication_action_check(username, layername):
    pass


def get_layer_info(username, layername):
    input_file_dir = qgis.get_layer_dir(username, layername)
    result = {}
    if os.path.exists(input_file_dir):
        result = {'name': layername}
    return result


def post_layer(username, layername, store_in_geoserver):
    if not store_in_geoserver:
        qgis.ensure_layer_dir(username, layername)
        shutil.copy('sample/qgis/project_8.qgis', get_layer_file_path(username, layername))


def patch_layer(username, layername):
    pass


def delete_layer(username, layername):
    qgis.delete_layer_dir(username, layername)


def get_layer_capabilities_url(username, layername):
    url = f'{settings.LAYMAN_QGIS_URL}?SERVICE=WMS&REQUEST=GetCapabilities&map={get_layer_file_path(username, layername)}'
    return url


def get_layer_file_path(username, layername):
    return os.path.join(qgis.get_layer_dir(username, layername), f'{layername}.qgis')
