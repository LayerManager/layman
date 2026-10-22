import pytest

from layman import settings
from test_tools import process_client
from tests.asserts.final.publication import geoserver_proxy

OWNER = 'test_wcs_access_owner'
OTHER_USER = 'test_wcs_access_other'
LAYER = 'test_wcs_private_raster'


@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
def test_wcs_forbidden_without_read():
    process_client.ensure_reserved_username(OWNER)
    process_client.ensure_reserved_username(OTHER_USER)

    post_response = process_client.publish_workspace_layer(
        OWNER,
        LAYER,
        file_paths=['sample/layman.layer/sample_tif_rgb.tif'],
        actor_name=OWNER,
        access_rights={'read': OWNER, 'write': OWNER},
    )
    uuid = post_response['uuid']
    try:
        geoserver_proxy.workspace_wcs_1_0_0_available_if_raster(
            OWNER, process_client.LAYER_TYPE, LAYER, actor_name=OWNER,
        )
        geoserver_proxy.workspace_wcs_1_0_0_forbidden_without_read(
            OWNER, process_client.LAYER_TYPE, LAYER, actor_name=OTHER_USER,
        )
        geoserver_proxy.workspace_wcs_1_0_0_forbidden_without_read(
            OWNER, process_client.LAYER_TYPE, LAYER, actor_name=settings.ANONYM_USER,
        )
    finally:
        process_client.delete_publication(process_client.LAYER_TYPE, uuid, actor_name=OWNER)
