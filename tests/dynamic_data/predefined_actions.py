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

_POST_ZIP_SHP_WITHOUT_PRJ_DEFINITION = {
    'file_paths': [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
    ],
    'compress': True,
}

POST_ZIP_SHP_WITHOUT_PRJ = {
    consts.KEY_CALL: Action(process_client.publish_workspace_publication, _POST_ZIP_SHP_WITHOUT_PRJ_DEFINITION),
    consts.KEY_CALL_EXCEPTION: {
        consts.KEY_EXCEPTION: LaymanError,
        consts.KEY_EXCEPTION_ASSERTS: [
            Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                          'code': 18,
                                                                          'message': 'Missing one or more ShapeFile files.',
                                                                          'detail': {
                                                                              'missing_extensions': ['.prj'],
                                                                              'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                                                                              'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp',
                                                                          },
                                                                          }, }, ),
        ],
    },
}

POST_ZIP_SHP_WITHOUT_PRJ_WITH_CRS = {
    consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
        **_POST_ZIP_SHP_WITHOUT_PRJ_DEFINITION,
        'crs': 'EPSG:4326',
    }),
    consts.KEY_RESPONSE_ASSERTS: [
        Action(processing.response.valid_post, dict()),
    ],
}
