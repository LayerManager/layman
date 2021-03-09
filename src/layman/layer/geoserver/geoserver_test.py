import pytest

from layman import settings
from layman.http import LaymanError
from test import process_client


@pytest.mark.usefixtures('ensure_layman')
def test_check_workspace_wms():
    workspace = 'test_check_workspace_wms_user' + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX
    layer = 'test_check_workspace_wms_layer'
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_layer(workspace, layer)
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 45
    assert exc_info.value.data['workspace_name'] == workspace


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_check_user_wms():
    user = 'test_check_user_wms' + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX
    auth_headers = process_client.get_authz_headers(user)
    with pytest.raises(LaymanError) as exc_info:
        process_client.reserve_username(user, headers=auth_headers)
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 45
    assert exc_info.value.data['workspace_name'] == user
