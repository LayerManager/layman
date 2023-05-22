from layman import app, settings, util as layman_util
from layman.layer.geoserver import util as gs_util
from test_tools import util as test_util, process_client
from . import geoserver_util


def is_complete_in_workspace_wms(workspace, publ_type, name, *, version, headers=None):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        wms_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX + '/ows')
    wms_inst = gs_util.wms_proxy(wms_url, version=version, headers=headers)
    validate_metadata_url = version != '1.1.1'
    geoserver_util.is_complete_in_workspace_wms_instance(wms_inst, name, validate_metadata_url=validate_metadata_url)


def is_complete_in_workspace_wms_1_3_0(workspace, publ_type, name, headers):
    assert publ_type == process_client.LAYER_TYPE
    is_complete_in_workspace_wms(workspace, publ_type, name, version='1.3.0', headers=headers)


def workspace_wfs_2_0_0_capabilities_available_if_vector(workspace, publ_type, name, headers):
    with app.app_context():
        internal_wfs_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + '/wfs')

    with app.app_context():
        file_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['geodata_type']})
    geodata_type = file_info['geodata_type']
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        wfs_inst = gs_util.wfs_proxy(wfs_url=internal_wfs_url, version='2.0.0', headers=headers)

        assert wfs_inst.contents
        wfs_name = f'{workspace}:{name}'
        assert wfs_name in wfs_inst.contents
        wfs_layer = wfs_inst.contents[wfs_name]
        assert len(wfs_layer.metadataUrls) == 1
        assert wfs_layer.metadataUrls[0]['url'].startswith('http://localhost:3080/record/xml/m-')
