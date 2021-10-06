from layman import LaymanError
import tests.asserts.processing as processing
from test_tools import process_client
from .. import dynamic_data as consts, Action

PATCH_TIF_WITH_QML = {
    consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
        'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
        'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
    }),
    consts.KEY_CALL_EXCEPTION: {
        consts.KEY_EXCEPTION: LaymanError,
        consts.KEY_EXCEPTION_ASSERTS: [
            Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                          'code': 48,
                                                                          'message': 'Wrong combination of parameters',
                                                                          'detail': 'Raster layers are not allowed to have QML style.',
                                                                          }, }, ),
        ],
    },
}

POST_TIF_WITH_QML = {**PATCH_TIF_WITH_QML, **{
    consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
        'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
        'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
    }),
}}
