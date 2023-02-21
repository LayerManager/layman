import pytest

from layman import LaymanError
from test_tools import process_client, util as test_util
from ... import static_data as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_RASTER_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_patch_raster_qml(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    expected_exc = {'http_code': 400,
                    'code': 48,
                    'message': 'Wrong combination of parameters',
                    'data': 'Raster layers are not allowed to have QML style.',
                    }

    headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])
    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_layer(workspace, publication, style_file='sample/style/ne_10m_admin_0_countries.qml', headers=headers)
    test_util.assert_error(expected_exc, exc_info)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_QML_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_patch_qml_raster(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    expected_exc = {'http_code': 400,
                    'code': 48,
                    'message': 'Wrong combination of parameters',
                    'data': 'Raster layers are not allowed to have QML style.',
                    }

    with pytest.raises(LaymanError) as exc_info:
        process_client.patch_workspace_layer(workspace, publication, file_paths=['sample/layman.layer/sample_tif_rgb.tif', ])
    test_util.assert_error(expected_exc, exc_info)
