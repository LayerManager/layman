from layman import app, settings, util as layman_util, names
from layman.layer.geoserver import util as gs_util
from layman.util import XForwardedClass
from test_tools import util as test_util, process_client, geoserver_client
from . import geoserver_util


def is_complete_in_workspace_wms(workspace, publ_type, name, *, version, headers=None):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        wms_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX + '/ows')
        uuid = layman_util.get_publication_uuid(workspace, publ_type, name)
    gs_layername = names.get_layer_names_by_source(uuid=uuid, ).wms.name
    wms_inst = gs_util.wms_proxy(wms_url, version=version, headers=headers)
    validate_metadata_url = version != '1.1.1'
    geoserver_util.is_complete_in_workspace_wms_instance(wms_inst, gs_layername, validate_metadata_url=validate_metadata_url)


def is_complete_in_workspace_wms_1_3_0(workspace, publ_type, name, headers=None, *, actor_name=None):
    headers = headers or {}
    assert headers is not None or actor_name is not None
    if actor_name:
        assert process_client.TOKEN_HEADER not in headers
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(process_client.get_authz_headers(actor_name))
    assert publ_type == process_client.LAYER_TYPE
    is_complete_in_workspace_wms(workspace, publ_type, name, version='1.3.0', headers=headers)


def workspace_wfs_2_0_0_capabilities_available_if_vector(workspace, publ_type, name, headers=None, *, actor_name=None):
    headers = headers or {}
    assert headers is not None or actor_name is not None
    if actor_name:
        assert process_client.TOKEN_HEADER not in headers
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(process_client.get_authz_headers(actor_name))
    with app.app_context():
        internal_wfs_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + '/wfs')

    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, publ_type, name)
        file_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['geodata_type']})
    geodata_type = file_info['geodata_type']
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        gs_layername = names.get_names_by_source(uuid=uuid, publication_type=publ_type).wfs.name
        wfs_inst = gs_util.wfs_proxy(wfs_url=internal_wfs_url, version='2.0.0', headers=headers)

        assert wfs_inst.contents
        wfs_name = f'{workspace}:{gs_layername}'
        assert wfs_name in wfs_inst.contents, "Layer not found in Capabilities."
        wfs_layer = wfs_inst.contents[wfs_name]
        assert len(wfs_layer.metadataUrls) == 1
        assert wfs_layer.metadataUrls[0]['url'].startswith('http://localhost:3080/record/xml/m-')


def wms_legend_url_with_x_forwarded_headers(workspace, publ_type, name, headers=None):
    assert publ_type == process_client.LAYER_TYPE
    x_forwarded_items = XForwardedClass(proto='https', host='abc.cz:4142', prefix='/layman-proxy')
    headers = headers or {}
    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, publ_type, name)
    gs_layername = names.get_layer_names_by_source(uuid=uuid, ).wms.name

    for input_workspace, key in [(workspace + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX, gs_layername),
                                 ('', f'{workspace + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}:{gs_layername}'), ]:
        for version in ['1.3.0', '1.1.1']:
            wms_inst = geoserver_client.get_wms_capabilities(input_workspace,
                                                             headers={**x_forwarded_items.headers,
                                                                      'X-Forwarded-Path': '/some-other-proxy',
                                                                      **headers,
                                                                      },
                                                             version=version,
                                                             )
            for style_content in wms_inst.contents[key].styles.values():
                assert style_content['legend'].startswith(f'https://abc.cz:4142/layman-proxy/geoserver/')
